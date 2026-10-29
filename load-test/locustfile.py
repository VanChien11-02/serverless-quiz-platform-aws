"""Two explicit Locust scenarios for the Serverless Quiz Week 4 project.

ReadOnlyStudent: 200 virtual clients with ONE shared Student token, GET /exams only.
FullExamStudent: up to 200 DISTINCT registered accounts from a LOCAL CSV; one exam each.

Do NOT run on sites or accounts other than your own authorized lab.
"""
import csv
import os

from gevent import sleep
from gevent.queue import Empty, Queue
from locust import HttpUser, between, task

EXAM_BASE = os.getenv("EXAM_API_BASE", "").rstrip("/")
ATTEMPT_BASE = os.getenv("ATTEMPT_API_BASE", "").rstrip("/")
EXAM_ID = os.getenv("LOAD_EXAM_ID", "EXAM001")
STUDENT_TOKEN = os.getenv("STUDENT_TOKEN", "")
STUDENTS_FILE = os.getenv("LOAD_STUDENTS_CSV", "load-test/test-students-local.csv")

ACCOUNT_QUEUE = Queue()
if os.path.isfile(STUDENTS_FILE):
    with open(STUDENTS_FILE, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("username") and row.get("password"):
                ACCOUNT_QUEUE.put((row["username"], row["password"]))


class ReadOnlyStudent(HttpUser):
    """Read-only performance test; not proof of 200 different identities or E2E exams."""
    host = EXAM_BASE or None
    wait_time = between(1, 3)

    @task
    def list_exams(self):
        if not STUDENT_TOKEN:
            raise RuntimeError("Set STUDENT_TOKEN first for ReadOnlyStudent")
        with self.client.get("/exams", name="GET /exams [read-only]", timeout=20,
                             headers={"Authorization": "Bearer " + STUDENT_TOKEN},
                             catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"Expected 200, received {res.status_code}")


class FullExamStudent(HttpUser):
    """Each virtual user logs in with a unique account and submits one exam exactly once."""
    host = EXAM_BASE or None
    wait_time = between(2, 4)

    def on_start(self):
        self.finished = False
        self.token = None
        try:
            username, password = ACCOUNT_QUEUE.get_nowait()
        except Empty:
            raise RuntimeError("No unused credentials left. Check CSV account count >= -u users")
        with self.client.post("/auth/login", json={"username": username, "password": password},
                              name="POST /auth/login", timeout=30, catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"Login HTTP {res.status_code}")
                self.finished = True
                return
            try:
                self.token = res.json()["accessToken"]
            except (KeyError, TypeError, ValueError):
                res.failure("Missing accessToken")
                self.finished = True

    @task
    def complete_one_exam(self):
        if self.finished:
            sleep(2)
            return
        self.finished = True  # Never start/submit the same virtual user twice.
        if not self.token or not ATTEMPT_BASE:
            return
        headers = {"Authorization": "Bearer " + self.token}

        with self.client.get("/exams", headers=headers, name="GET /exams [E2E]",
                             timeout=20, catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"GET /exams HTTP {res.status_code}")
                return

        with self.client.post(f"{ATTEMPT_BASE}/exams/{EXAM_ID}/start", json={},
                              headers=headers, name="POST /exams/{id}/start", timeout=25,
                              catch_response=True) as res:
            if res.status_code != 201:
                res.failure(f"Start HTTP {res.status_code}")
                return
            try:
                body = res.json()
                sid = body["submissionId"]
                questions = body["questions"]
                answers = {q["questionId"]: "A" for q in questions}
                if not answers:
                    raise ValueError("Exam has no questions")
            except (ValueError, KeyError, TypeError):
                res.failure("Start response invalid")
                return

        with self.client.post(f"{ATTEMPT_BASE}/submissions/{sid}/submit",
                              json={"answers": answers}, headers=headers,
                              name="POST /submissions/{id}/submit", timeout=25,
                              catch_response=True) as res:
            if res.status_code not in (202, 200):
                res.failure(f"Submit HTTP {res.status_code}")
                return

        # Poll result after submission because grading via SQS is asynchronous.
        for attempt in range(10):
            sleep(2)
            with self.client.get(f"{ATTEMPT_BASE}/submissions/{sid}/result",
                                 headers=headers, name="GET /submissions/{id}/result",
                                 timeout=25, catch_response=True) as res:
                if res.status_code != 200:
                    res.failure(f"Result HTTP {res.status_code}")
                    return
                try:
                    status = res.json().get("status")
                except (ValueError, TypeError):
                    res.failure("Bad result JSON")
                    return
                if status == "COMPLETED":
                    return
                if status not in ("SUBMITTED", "IN_PROGRESS"):
                    res.failure(f"Unexpected result status: {status}")
                    return
                if attempt == 9:
                    res.failure("Not COMPLETED within polling window (20 seconds)")
                    return
