"""Local isolated tests: no AWS credentials and no real AWS calls."""
import importlib.util
import json
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def import_attempt():
    p = ROOT / 'lambda/submit/quiz_submit_handler.py'
    spec = importlib.util.spec_from_file_location('quiz_submit_week3_mock', p)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {'EXAMS_TABLE':'Exams','QUESTIONS_TABLE':'Questions',
                                  'SUBMISSIONS_TABLE':'Submissions','GRADING_QUEUE_URL':'https://example.invalid/q'}), \
         patch('boto3.resource'), patch('boto3.client'):
        spec.loader.exec_module(mod)
    return mod


def event(method, path, role, user):
    return {'requestContext': {'http': {'method': method}, 'authorizer': {'lambda':
            {'role': role, 'userId':user}}}, 'rawPath': path,
            'body': json.dumps({'studentId':'someone_else', 'answers':{}})}


class RBACChecks(TestCase):
    def test_admin_cannot_start_student_exam(self):
        mod = import_attempt()
        resp = mod.lambda_handler(event('POST','/exams/EXAM001/start','Admin','admin01'),None)
        self.assertEqual(resp['statusCode'],403)

    def test_student_id_taken_from_jwt_not_body(self):
        mod = import_attempt()
        with patch.object(mod,'start_exam', return_value={'statusCode':201}) as fn:
            resp=mod.lambda_handler(event('POST','/exams/EXAM001/start','Student','student01'),None)
            self.assertEqual(resp['statusCode'],201)
            fn.assert_called_once_with('EXAM001','student01')

    def test_student_cannot_read_anothers_result(self):
        mod = import_attempt()
        with patch.object(mod,'get_submission',return_value={'studentId':'student01'}):
            resp = mod.lambda_handler(event('GET','/submissions/abc/result','Student','student02'),None)
        self.assertEqual(resp['statusCode'],403)

    def test_student_cannot_submit_anothers_exam(self):
        mod = import_attempt()
        with patch.object(mod,'get_submission',return_value={'studentId':'student01'}):
            resp = mod.lambda_handler(event('POST','/submissions/abc/submit','Student','student02'),None)
        self.assertEqual(resp['statusCode'],403)
