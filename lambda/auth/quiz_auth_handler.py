import base64
import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from lambda.auth.jwt_utils import make_token

logger = logging.getLogger(__name__)
users = boto3.resource('dynamodb').Table(os.environ['USERS_TABLE'])
ITERATIONS = 600_000


def respond(status, data):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(data)}


def request_body(event):
    if event.get('isBase64Encoded'):
        raise ValueError('unsupported encoding')
    raw = event.get('body') or '{}'
    if not isinstance(raw, str):
        raise ValueError('body must be JSON')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('JSON object required')
    return data


def username_of(value):
    if not isinstance(value, str):
        return None
    name = value.strip().lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,30}', name):
        return None
    return name


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)


def register(data):
    username = username_of(data.get('username'))
    password = data.get('password')
    if 'role' in data:
        return respond(400, {'error': 'Public registration cannot assign a role'})
    if not username or not isinstance(password, str) or not (10 <= len(password) <= 128):
        return respond(400, {'error': 'Invalid username or password (minimum 10 characters)'})
    salt = os.urandom(16)
    item = {'userId': username, 'role': 'Student',
            'passwordSalt': base64.b64encode(salt).decode(),
            'passwordHash': base64.b64encode(hash_password(password, salt)).decode(),
            'passwordIterations': ITERATIONS,
            'createdAt': datetime.now(timezone.utc).isoformat()}
    try:
        users.put_item(Item=item, ConditionExpression='attribute_not_exists(userId)')
    except users.meta.client.exceptions.ConditionalCheckFailedException:
        return respond(409, {'error': 'Username already exists'})
    return respond(201, {'userId': username, 'role': 'Student'})


def login(data):
    username = username_of(data.get('username'))
    password = data.get('password')
    if not username or not isinstance(password, str):
        return respond(401, {'error': 'Invalid credentials'})
    item = users.get_item(Key={'userId': username}, ConsistentRead=True).get('Item')
    if not item:
        return respond(401, {'error': 'Invalid credentials'})
    try:
        iterations = int(item['passwordIterations'])
        if iterations != ITERATIONS:  # educational demo: one supported hash policy
            return respond(401, {'error': 'Invalid credentials'})
        salt = base64.b64decode(item['passwordSalt'], validate=True)
        expected = base64.b64decode(item['passwordHash'], validate=True)
        actual = hash_password(password, salt)
        if not hmac.compare_digest(actual, expected):
            return respond(401, {'error': 'Invalid credentials'})
        role = item['role']
        token, ttl = make_token(username, role)
    except (KeyError, ValueError, TypeError):
        return respond(401, {'error': 'Invalid credentials'})
    return respond(200, {'accessToken': token, 'tokenType': 'Bearer',
                         'expiresIn': ttl, 'role': role, 'userId': username})


def lambda_handler(event, context):
    method = (event.get('requestContext', {}).get('http', {}).get('method')
              or event.get('httpMethod') or '').upper()
    path = (event.get('rawPath') or event.get('path') or '').rstrip('/')
    try:
        if method == 'POST' and path == '/auth/register':
            return register(request_body(event))
        if method == 'POST' and path == '/auth/login':
            return login(request_body(event))
        return respond(404, {'error': 'Route not found'})
    except (ValueError, TypeError, json.JSONDecodeError):
        return respond(400, {'error': 'Invalid JSON request'})
    except ClientError:
        logger.exception('Auth DynamoDB failure')
        return respond(500, {'error': 'Internal server error'})
