"""Mocked unit tests: no AWS calls made. Run: python -m unittest discover -s tests"""
import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SUBMISSIONS_TABLE', 'Submissions')
os.environ.setdefault('REPORTS_BUCKET', 'quiz-local-test-bucket')
os.environ['AWS_EC2_METADATA_DISABLED'] = 'true'

spec = importlib.util.spec_from_file_location('export_lambda', str(Path(__file__).parents[1] / 'lambda' / 'export' / 'lambda_function.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def event(role, user='admin01', body='{"examId":"EXAM001"}'):
    return {'version': '2.0', 'rawPath':'/reports/export', 'body':body,
            'requestContext': {'http': {'method':'POST'},
                               'authorizer':{'lambda':{'role':role,'userId':user}}}}


class FakeTable:
    def __init__(self):
        self.calls = 0
    def scan(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {'Items':[{'submissionId':'sub1','examId':'EXAM001','studentId':'student01',
                              'correctCount':2,'totalQuestions':3,'score':'6.67',
                              'status':'COMPLETED','gradedAt':'2026-10-27'}],
                    'LastEvaluatedKey': {'submissionId':'sub1'}}
        return {'Items':[{'submissionId':'sub2','examId':'EXAM001','studentId':'=malicious',
                          'correctCount':1,'totalQuestions':3,'score':'3.33',
                          'status':'COMPLETED','gradedAt':'2026-10-28'}]}


class FakeDynamo:
    def __init__(self): self.table = FakeTable()
    def Table(self, name): return self.table


class FakeS3:
    def __init__(self): self.calls=[]
    def put_object(self, **kwargs): self.calls.append(kwargs)


class TestExport(unittest.TestCase):
    def test_student_forbidden(self):
        self.assertEqual(mod.lambda_handler(event('Student'), None)['statusCode'], 403)
    def test_missing_auth(self):
        self.assertEqual(mod.lambda_handler({'rawPath':'/reports/export', 'requestContext':{'http':{'method':'POST'}}}, None)['statusCode'], 401)
    def test_malformed_input(self):
        self.assertEqual(mod.lambda_handler(event('Admin',body='{"examId":"../../oops"}'), None)['statusCode'], 400)
    def test_admin_csv_pagination_and_safety(self):
        ddb, s3 = FakeDynamo(), FakeS3()
        with patch.object(mod.boto3,'resource',return_value=ddb), patch.object(mod.boto3,'client',return_value=s3):
            result = mod.lambda_handler(event('Admin'), None)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body'])['rows'], 2)
        self.assertEqual(ddb.table.calls, 2)
        payload = s3.calls[0]['Body'].decode('utf-8-sig')
        self.assertIn('6.67',payload)
        self.assertIn("'=malicious",payload)
        self.assertNotIn('answerKey',payload)
        self.assertEqual(s3.calls[0]['ServerSideEncryption'],'AES256')


if __name__=='__main__': unittest.main()
