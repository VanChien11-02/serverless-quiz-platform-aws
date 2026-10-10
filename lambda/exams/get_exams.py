import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Exams")


def lambda_handler(event, context):
    try:
        path_parameters = event.get("pathParameters") or {}
        exam_id = path_parameters.get("examId")

        # GET /exams/{examId}
        if exam_id:
            response = table.get_item(
                Key={
                    "examId": exam_id
                }
            )

            item = response.get("Item")

            if not item:
                return {
                    "statusCode": 404,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps({
                        "message": "Exam not found"
                    })
                }

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(item, default=str)
            }

        # GET /exams
        response = table.scan()
        items = response.get("Items", [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(items, default=str)
        }

    except Exception as e:
        print(e)

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Internal server error"
            })
        }