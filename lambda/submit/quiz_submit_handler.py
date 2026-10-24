import json
import logging
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
exams_table = dynamodb.Table(os.environ["EXAMS_TABLE"])
questions_table = dynamodb.Table(os.environ["QUESTIONS_TABLE"])
submissions_table = dynamodb.Table(os.environ["SUBMISSIONS_TABLE"])
sqs = boto3.client("sqs")
queue_url = os.environ["GRADING_QUEUE_URL"]


def json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Unsupported JSON value type: {type(value).__name__}")


def respond(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False, default=json_default),
    }


def get_body(event):
    if event.get("isBase64Encoded"):
        raise ValueError("Base64 request bodies are not supported")
    raw = event.get("body") or "{}"
    if not isinstance(raw, str):
        raise ValueError("Body must be a JSON string")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("JSON body must be an object")
    return obj


def get_submission(submission_id):
    return submissions_table.get_item(Key={"submissionId": submission_id}, ConsistentRead=True).get("Item")


def start_exam(exam_id, student_id):
    # student_id is verified identity from the authorizer, NEVER client body.

    exam = exams_table.get_item(Key={"examId": exam_id}, ConsistentRead=True).get("Item")
    if not exam:
        return respond(404, {"error": "Exam not found"})

    duration = int(exam.get("duration", 0))
    if not 1 <= duration <= 180:
        return respond(400, {"error": "Exam duration must be between 1 and 180 minutes"})

    # Query based on QuizQuestions PK=examId, SK=questionId; demo max 100 questions.
    result = questions_table.query(
        KeyConditionExpression=Key("examId").eq(exam_id), Limit=101
    )
    items = result.get("Items", [])
    if len(items) > 100 or "LastEvaluatedKey" in result:
        return respond(400, {"error": "This demo supports at most 100 questions"})
    if not items:
        return respond(400, {"error": "This exam has no questions"})

    for item in items:
        if (not item.get("questionId") or not isinstance(item.get("options"), dict)
                or item.get("correctAnswer") not in ("A", "B", "C", "D")):
            return respond(500, {"error": "Exam question data is invalid"})

    # cryptographically secure random ordering; same order by chance is possible.
    secrets.SystemRandom().shuffle(items)
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=duration)
    submission_id = str(uuid.uuid4())
    question_order = [row["questionId"] for row in items]
    # Answer snapshot prevents edits to the question bank from changing this exam result.
    answer_key = {row["questionId"]: row["correctAnswer"] for row in items}
    submission = {
        "submissionId": submission_id,
        "examId": exam_id,
        "studentId": student_id.strip(),
        "status": "IN_PROGRESS",
        "startedAt": now.isoformat(),
        "expiresAt": expiry.isoformat(),
        "expiresAtEpoch": int(expiry.timestamp()),
        "questionOrder": question_order,
        "answerKey": answer_key,  # PRIVATE: never return this or the raw item to students.
    }
    submissions_table.put_item(Item=submission, ConditionExpression="attribute_not_exists(submissionId)")

    questions_for_student = [
        {
            "questionId": row["questionId"],
            "content": row.get("content", ""),
            "options": row["options"],
        }
        for row in items
    ]
    return respond(201, {
        "submissionId": submission_id,
        "examId": exam_id,
        "status": "IN_PROGRESS",
        "startedAt": now.isoformat(),
        "expiresAt": expiry.isoformat(),
        "duration": duration,
        "questions": questions_for_student,
    })


def mark_expired(submission_id):
    # Conditional update prevents overwriting a submitted/completed submission.
    try:
        submissions_table.update_item(
            Key={"submissionId": submission_id},
            UpdateExpression="SET #st = :expired",
            ConditionExpression="#st = :in_progress",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":expired": "EXPIRED", ":in_progress": "IN_PROGRESS"
            },
        )
    except submissions_table.meta.client.exceptions.ConditionalCheckFailedException:
        pass


def send_to_grading_queue(submission_id):
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"submissionId": submission_id}),
    )


def submit_exam(submission_id, body, student_id):
    answers = body.get("answers")
    if not isinstance(answers, dict):
        return respond(400, {"error": "answers must be a JSON object"})

    submission = get_submission(submission_id)
    if not submission:
        return respond(404, {"error": "submission not found"})
    if submission.get("studentId") != student_id:
        return respond(403, {"error": "Not your submission"})

    valid_ids = set(submission.get("questionOrder", []))
    if (not valid_ids or len(answers) > len(valid_ids)
            or any(key not in valid_ids or value not in ("A", "B", "C", "D")
                   for key, value in answers.items())):
        return respond(400, {"error": "Invalid question ID or answer (A, B, C, D)"})

    status = submission.get("status")
    if status == "COMPLETED":
        return respond(200, {"submissionId": submission_id, "status": "COMPLETED"})
    if status == "EXPIRED":
        return respond(409, {"error": "Exam time has expired"})
    if status == "SUBMITTED":
        # Allow a safe retry after a temporary SQS failure. Never change saved answers.
        if submission.get("answers", {}) != answers:
            return respond(409, {"error": "submission already submitted with different answers"})
    elif status == "IN_PROGRESS":
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        if now_epoch >= int(submission["expiresAtEpoch"]):
            mark_expired(submission_id)
            return respond(409, {"error": "Exam time has expired"})
        try:
            submissions_table.update_item(
                Key={"submissionId": submission_id},
                UpdateExpression=(
                    "SET #st = :submitted, answers = :answers, "
                    "submittedAt = :submitted_at"
                ),
                ConditionExpression=(
                    "#st = :in_progress AND expiresAtEpoch > :now"
                ),
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":submitted": "SUBMITTED",
                    ":in_progress": "IN_PROGRESS",
                    ":answers": answers,
                    ":submitted_at": datetime.now(timezone.utc).isoformat(),
                    ":now": now_epoch,
                },
            )
        except submissions_table.meta.client.exceptions.ConditionalCheckFailedException:
            return respond(409, {"error": "Already submitted or exam time expired"})
    else:
        return respond(409, {"error": "submission cannot be submitted in this state"})

    # This may be delivered more than once; the worker is idempotent.
    try:
        send_to_grading_queue(submission_id)
    except ClientError:
        logger.exception("SQS send failed for submission %s", submission_id)
        return respond(503, {
            "error": "Submission saved but could not queue grading; retry the SAME request",
            "submissionId": submission_id,
            "status": "SUBMITTED",
        })
    return respond(202, {"submissionId": submission_id, "status": "SUBMITTED"})


def get_result(submission_id, student_id):
    submission = get_submission(submission_id)
    if not submission:
        return respond(404, {"error": "submission not found"})
    if submission.get("studentId") != student_id:
        return respond(403, {"error": "Not your submission"})

    status = submission.get("status")
    if status == "IN_PROGRESS" and int(datetime.now(timezone.utc).timestamp()) >= int(submission["expiresAtEpoch"]):
        mark_expired(submission_id)
        submission = get_submission(submission_id)
        status = submission.get("status")

    payload = {"submissionId": submission_id, "examId": submission["examId"], "status": status}
    if status == "COMPLETED":
        payload.update({
            "correctCount": submission["correctCount"],
            "totalQuestions": submission["totalQuestions"],
            "score": submission["score"],
            "gradedAt": submission["gradedAt"],
        })
    return respond(200, payload)


def lambda_handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod") or "").upper()
    path = (event.get("rawPath") or event.get("path") or "").rstrip("/")

    principal = ((event.get("requestContext") or {}).get("authorizer") or {}).get("lambda") or {}
    if not principal.get("userId") or principal.get("role") not in ("Student", "Admin"):
        return respond(401, {"error": "Authentication required"})
    if principal.get("role") != "Student":
        return respond(403, {"error": "Student role required"})
    student_id = principal["userId"]

    try:
        start_match = re.fullmatch(r"/exams/([^/]+)/start", path)
        submit_match = re.fullmatch(r"/submissions/([^/]+)/submit", path)
        result_match = re.fullmatch(r"/submissions/([^/]+)/result", path)

        if method == "POST" and start_match:
            return start_exam(start_match.group(1), student_id)
        if method == "POST" and submit_match:
            return submit_exam(submit_match.group(1), get_body(event), student_id)
        if method == "GET" and result_match:
            return get_result(result_match.group(1), student_id)
        return respond(404, {"error": "Route not found"})
    except (ValueError, TypeError, json.JSONDecodeError):
        return respond(400, {"error": "Invalid request body or data"})
    except ClientError:
        logger.exception("AWS service error")
        return respond(500, {"error": "AWS service error; check CloudWatch Logs"})
    except Exception:
        logger.exception("Unexpected error")
        return respond(500, {"error": "Internal server error; check CloudWatch Logs"})
