import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / 'lambda' / 'auth'
sys.path.insert(0, str(SRC))
import jwt_utils

class JwtTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'JWT_SECRET': 'demo-secret-never-use-in-production-0123456789',
                                           'JWT_TTL_SECONDS': '3600'})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_valid_token(self):
        token, ttl = jwt_utils.make_token('student01', 'Student')
        self.assertEqual(ttl, 3600)
        self.assertEqual(jwt_utils.verify_token(token), {'userId':'student01','role':'Student'})

    def test_tampering_fails(self):
        token, _ = jwt_utils.make_token('student01', 'Student')
        a, b, c = token.split('.')
        self.assertIsNone(jwt_utils.verify_token(a + '.' + b + '.' + ('A' if c[0] != 'A' else 'B') + c[1:]))

    def test_expired_token(self):
        with patch('jwt_utils.time.time', return_value=1000):
            token, _ = jwt_utils.make_token('student01', 'Student')
        with patch('jwt_utils.time.time', return_value=4601):
            self.assertIsNone(jwt_utils.verify_token(token))

    def test_wrong_secret(self):
        token, _ = jwt_utils.make_token('student01', 'Student')
        os.environ['JWT_SECRET'] = 'a-different-secret-length-over-32-bytes-12345'
        self.assertIsNone(jwt_utils.verify_token(token))

if __name__ == '__main__':
    unittest.main()
