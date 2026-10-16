import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
submissions_table = dynamodb.Table(os.environ["SUBMISSIONS_TABLE"])


def grade_submission(submission_id):
    submission = submissions_table.get_item(
        Key={"submissionId": submission_id}, ConsistentRead=True
    ).get("Item")
    if submission is None:
        raise ValueError(f"submission not found: {submission_id}")

    status = submission.get("status")
    if status == "COMPLETED":
        logger.info("Duplicate message ignored for completed submission %s", submission_id)
        return
    if status != "SUBMITTED":
        raise ValueError(f"Unexpected submission status {status} for {submission_id}")

    order = submission["questionOrder"]
    key = submission["answerKey"]
    answers = submission.get("answers", {})
    total = len(order)
    if total == 0:
        raise ValueError(f"submission contains zero questions: {submission_id}")

    correct = sum(1 for question_id in order if answers.get(question_id) == key[question_id])
    score = (Decimal(correct) * Decimal("10") / Decimal(total)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    try:
        submissions_table.update_item(
            Key={"submissionId": submission_id},
            UpdateExpression=(
                "SET #st = :done, correctCount = :correct, "
                "totalQuestions = :total, score = :score, gradedAt = :graded_at"
            ),
            ConditionExpression="#st = :submitted",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":done": "COMPLETED",
                ":submitted": "SUBMITTED",
                ":correct": correct,
                ":total": total,
                ":score": score,
                ":graded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info("Graded submission %s with %s/%s correct", submission_id, correct, total)
    except submissions_table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.info("Another worker already graded submission %s", submission_id)


def lambda_handler(event, context):
    # With BatchSize=1, a failing message can be retried independently.
    for record in event.get("Records", []):
        message = json.loads(record["body"])
        submission_id = message.get("submissionId")
        if not isinstance(submission_id, str) or not submission_id:
            raise ValueError("SQS message missing submissionId")
        grade_submission(submission_id)
    return {"processedRecords": len(event.get("Records", []))}
