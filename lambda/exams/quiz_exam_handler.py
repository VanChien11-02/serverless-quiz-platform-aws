import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")

exams = dynamodb.Table(os.environ["EXAMS_TABLE"])
questions = dynamodb.Table(os.environ["QUESTIONS_TABLE"])



def convert_decimal(obj):
    if isinstance(obj, Decimal):
        if obj == obj.to_integral_value():
            return int(obj)
        return float(obj)

    raise TypeError(
        f"Type {type(obj).__name__} is not JSON serializable"
    )


def response(status, data):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(
            data,
            ensure_ascii=False,
            default=convert_decimal
        )
    }


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def create_exam(body):
    title = body.get("title")
    duration = body.get("duration")

    if not isinstance(title, str) or not title.strip():
        return response(400, {"error": "Invalid title"})

    if type(duration) is not int or duration <= 0:
        return response(400, {"error": "Invalid duration"})

    exam = {
        "examId": str(uuid.uuid4()),
        "title": title.strip(),
        "duration": duration,
        "createdAt": now_utc()
    }

    exams.put_item(Item=exam)

    return response(201, exam)


def list_exams():
    # Demo: danh sach nho. Pagination se bo sung sau.
    result = exams.scan(Limit=100)

    return response(200, {
        "items": result.get("Items", [])
    })


def get_exam(exam_id):
    result = exams.get_item(
        Key={"examId": exam_id}
    )

    exam = result.get("Item")

    if not exam:
        return response(404, {"error": "Exam not found"})

    return response(200, exam)


def add_question(exam_id, body):
    exam = exams.get_item(Key={"examId": exam_id})

    if "Item" not in exam:
        return response(404, {"error": "Exam not found"})

    content = body.get("content")
    options = body.get("options")
    answer = body.get("correctAnswer")

    if not isinstance(content, str) or not content.strip():
        return response(400, {"error": "Invalid content"})

    if not isinstance(options, dict):
        return response(400, {"error": "Invalid options"})

    if set(options.keys()) != {"A", "B", "C", "D"}:
        return response(400, {"error": "Expected options A B C D"})

    if not all(isinstance(v, str) and v.strip()
               for v in options.values()):
        return response(400, {"error": "Invalid option value"})

    if answer not in ("A", "B", "C", "D"):
        return response(400, {"error": "Invalid answer"})

    question = {
        "examId": exam_id,
        "questionId": str(uuid.uuid4()),
        "content": content.strip(),
        "options": options,
        "correctAnswer": answer
    }

    questions.put_item(Item=question)

    # Khong tra dap an dung trong response
    public_question = {
        k: v for k, v in question.items()
        if k != "correctAnswer"
    }

    return response(201, public_question)


def lambda_handler(event, context):
    method = (
        event.get("requestContext", {})
             .get("http", {})
             .get("method")
        or event.get("httpMethod")
    )

    path = event.get("rawPath") or event.get("path", "")
    params = event.get("pathParameters") or {}
    exam_id = params.get("id") or params.get("examId")

    # Context is populated by API Gateway HTTP API Lambda authorizer (payload v2.0).
    principal = ((event.get("requestContext") or {}).get("authorizer") or {}).get("lambda") or {}
    role = principal.get("role")
    if role not in ("Admin", "Student") or not principal.get("userId"):
        return response(401, {"error": "Authentication required"})
    if method == "POST" and role != "Admin":
        return response(403, {"error": "Admin role required"})

    try:
        if method == "GET" and path.rstrip("/") == "/exams":
            return list_exams()

        if method == "GET" and exam_id:
            return get_exam(exam_id)

        body = json.loads(event.get("body") or "{}")

        if not isinstance(body, dict):
            return response(400, {"error": "Expected JSON object"})

        if method == "POST" and path.rstrip("/") == "/exams":
            return create_exam(body)

        if method == "POST" and exam_id:
            return add_question(exam_id, body)

        return response(404, {"error": "Route not found"})

    except (ValueError, TypeError):
        return response(400, {"error": "Invalid JSON"})

    except ClientError as e:
        print("AWS error:", str(e))
        return response(500, {"error": "Database error"})
