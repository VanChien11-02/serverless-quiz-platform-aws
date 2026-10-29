"""Admin-only export of COMPLETED submissions to a private S3 CSV object.
HTTP API Lambda proxy integration, payload format 2.0.
Environment: SUBMISSIONS_TABLE, REPORTS_BUCKET, AWS_REGION (provided by Lambda).
"""
import csv
import io
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

FIELDS = [
    "submissionId", "examId", "studentId", "correctCount",
    "totalQuestions", "score", "status", "gradedAt",
]


def respond(code, obj):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(obj, ensure_ascii=False),
    }


def safe_csv_cell(value):
    """Avoid spreadsheet formula injection if an identifier starts with a formula marker."""
    if value is None:
        return ""
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def parse_exam_id(event):
    if event.get("isBase64Encoded"):
        raise ValueError("Base64 body is not supported")
    raw = event.get("body") or "{}"
    if not isinstance(raw, str):
        raise ValueError("JSON body is required")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON object is required")
    exam_id = data.get("examId")
    if not isinstance(exam_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", exam_id):
        raise ValueError("examId must be a 1-80 character identifier")
    return exam_id


def export_completed(exam_id):
    table_name = os.environ["SUBMISSIONS_TABLE"]
    bucket = os.environ["REPORTS_BUCKET"]
    table = boto3.resource("dynamodb").Table(table_name)

    # Return only CSV fields: never export answerKey, answers, questionOrder or password data.
    columns = {f"#f{i}": field for i, field in enumerate(FIELDS)}
    args = {
        "FilterExpression": Attr("examId").eq(exam_id) & Attr("status").eq("COMPLETED"),
        "ProjectionExpression": ", ".join(columns.keys()),
        "ExpressionAttributeNames": columns,
    }
    rows = []
    while True:
        result = table.scan(**args)
        rows.extend(result.get("Items", []))
        if "LastEvaluatedKey" not in result:
            break
        args["ExclusiveStartKey"] = result["LastEvaluatedKey"]

    if not rows:
        return respond(404, {"error": "No COMPLETED submissions found for examId"})

    rows.sort(key=lambda item: (str(item.get("gradedAt", "")), str(item.get("submissionId", ""))))
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\r\n")
    writer.writeheader()
    for item in rows:
        writer.writerow({key: safe_csv_cell(item.get(key)) for key in FIELDS})
    csv_bytes = out.getvalue().encode("utf-8-sig")  # Excel recognizes Vietnamese Unicode.

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"reports/{exam_id}/results-{stamp}-{uuid.uuid4().hex[:8]}.csv"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_bytes,
        ContentType="text/csv; charset=utf-8",
        ServerSideEncryption="AES256",
    )
    logger.info("Exported %d results for exam %s to S3", len(rows), exam_id)
    return respond(200, {"message": "CSV export completed", "examId": exam_id,
                         "rows": len(rows), "bucket": bucket, "key": key})


def lambda_handler(event, context):
    request = event.get("requestContext") or {}
    principal = ((request.get("authorizer") or {}).get("lambda") or {})
    if not principal.get("userId") or principal.get("role") not in ("Admin", "Student"):
        return respond(401, {"error": "Authentication required"})
    if principal.get("role") != "Admin":
        return respond(403, {"error": "Admin role required"})

    method = ((request.get("http") or {}).get("method") or event.get("httpMethod") or "").upper()
    path = (event.get("rawPath") or event.get("path") or "").rstrip("/")
    if method != "POST" or path != "/reports/export":
        return respond(404, {"error": "Route not found"})
    try:
        return export_completed(parse_exam_id(event))
    except (ValueError, TypeError, json.JSONDecodeError):
        return respond(400, {"error": "Invalid JSON or examId"})
    except (ClientError, KeyError):
        logger.exception("Failed to export report")
        return respond(500, {"error": "Export failed; check CloudWatch logs and permissions"})
