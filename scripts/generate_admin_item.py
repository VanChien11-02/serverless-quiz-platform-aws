"""Generate a DynamoDB JSON item for the first Admin; does not use AWS credentials.
Run locally: python scripts/generate_admin_item.py
Do not commit or publish admin-item.json (contains password hash).
"""
import base64
import getpass
import hashlib
import json
import os
import re
import sys

username = input('Admin username (3-30 chars, a-z0-9_.-): ').strip().lower()
if not re.fullmatch(r'[a-z0-9_.-]{3,30}', username):
    sys.exit('Invalid username')
password = getpass.getpass('Admin password (10+ chars): ')
if not (10 <= len(password) <= 128):
    sys.exit('Password must be between 10 and 128 characters')
salt = os.urandom(16)
digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600_000)
item = {'userId': {'S': username}, 'role': {'S': 'Admin'},
        'passwordSalt': {'S': base64.b64encode(salt).decode()},
        'passwordHash': {'S': base64.b64encode(digest).decode()},
        'passwordIterations': {'N': '600000'}}
# Save DynamoDB AttributeValue JSON as UTF-8. Do not put it into Git.
from pathlib import Path
output = Path('admin-item.json')
if output.exists():
    sys.exit('admin-item.json already exists; move it away before generating a new admin')
output.write_text(json.dumps(item, indent=2), encoding='utf-8')
print('Created admin-item.json (do not commit or share it)')
