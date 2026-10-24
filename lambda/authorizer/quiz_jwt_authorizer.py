"""HTTP API REQUEST Lambda authorizer; payload version 2.0, simple response."""
from jwt_utils import verify_token


def lambda_handler(event, context):
    headers = event.get('headers') or {}
    authorization = next((v for k, v in headers.items() if k.lower() == 'authorization'), '')
    if not isinstance(authorization, str):
        return {'isAuthorized': False}
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return {'isAuthorized': False}
    principal = verify_token(parts[1])
    return {'isAuthorized': True, 'context': principal} if principal else {'isAuthorized': False}
