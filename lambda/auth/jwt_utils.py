"""Minimal HS256 JWT helpers for an AWS Learner Lab capstone.
Use a maintained JWT library and a managed secret in real production systems.
"""
import base64
import hashlib
import hmac
import json
import os
import time

ISSUER = 'serverless-quiz-lab'
AUDIENCE = 'quiz-api'


def _secret():
    secret = os.environ.get('JWT_SECRET', '')
    if len(secret.encode('utf-8')) < 32:
        raise RuntimeError('JWT_SECRET must be at least 32 UTF-8 bytes')
    return secret.encode('utf-8')


def _encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _decode(data):
    if not isinstance(data, str) or not data or len(data) > 8192:
        raise ValueError('Invalid base64url')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in data):
        raise ValueError('Invalid base64url alphabet')
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


def make_token(user_id, role):
    if role not in ('Admin', 'Student') or not isinstance(user_id, str) or not user_id:
        raise ValueError('Invalid principal')
    ttl = int(os.environ.get('JWT_TTL_SECONDS', '3600'))
    if ttl < 1 or ttl > 86400:
        raise ValueError('JWT_TTL_SECONDS must be between 1 and 86400')
    now = int(time.time())
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'sub': user_id, 'role': role, 'iss': ISSUER, 'aud': AUDIENCE,
               'iat': now, 'exp': now + ttl}
    a = _encode(json.dumps(header, separators=(',', ':'), sort_keys=True).encode())
    b = _encode(json.dumps(payload, separators=(',', ':'), sort_keys=True).encode())
    signing_input = (a + '.' + b).encode('ascii')
    signature = _encode(hmac.new(_secret(), signing_input, hashlib.sha256).digest())
    return a + '.' + b + '.' + signature, ttl


def verify_token(token):
    try:
        if not isinstance(token, str) or len(token) > 8192:
            return None
        a, b, c = token.split('.')
        header = json.loads(_decode(a))
        claims = json.loads(_decode(b))
        if header != {'alg': 'HS256', 'typ': 'JWT'} or not isinstance(claims, dict):
            return None
        expected = hmac.new(_secret(), (a + '.' + b).encode('ascii'), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode(c)):
            return None
        now = int(time.time())
        exp, iat = claims.get('exp'), claims.get('iat')
        if type(exp) is not int or type(iat) is not int or exp <= now or iat > now + 30:
            return None
        if claims.get('iss') != ISSUER or claims.get('aud') != AUDIENCE:
            return None
        sub, role = claims.get('sub'), claims.get('role')
        if not isinstance(sub, str) or not (3 <= len(sub) <= 30):
            return None
        if role not in ('Admin', 'Student'):
            return None
        return {'userId': sub, 'role': role}
    except (ValueError, UnicodeError, TypeError, AttributeError, OverflowError):
        return None
