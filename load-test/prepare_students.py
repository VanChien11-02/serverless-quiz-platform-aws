"""Register distinct Student accounts for an authorized load test. Local use only.
Credentials are saved to a local CSV. NEVER commit this file or print passwords.
"""
import argparse
import csv
import datetime
import os
import re
import secrets
import sys
import time

import requests


def main():
    parser = argparse.ArgumentParser(description="Prepare Student test accounts using POST /auth/register")
    parser.add_argument("--base-url", default=os.getenv("EXAM_API_BASE"), help="Exam API base URL")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--prefix", default="w4" + datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%H%M"))
    parser.add_argument("--out", default="load-test/test-students-local.csv")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between registrations")
    args = parser.parse_args()
    if not args.base_url or not args.base_url.startswith("https://"):
        parser.error("--base-url must be a real HTTPS Exam API URL")
    if not 1 <= args.count <= 200:
        parser.error("--count must be between 1 and 200")
    if not re.fullmatch(r"[a-z][a-z0-9_-]{2,20}", args.prefix):
        parser.error("--prefix must be lowercase 3-21 chars (letters, numbers, _ or -)")
    if os.path.exists(args.out):
        parser.error(f"Output already exists: {args.out}. Choose another --prefix and --out")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    print(f"Registering {args.count} synthetic students. Save credentials locally at {args.out}.")
    with open(args.out, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["username", "password"])
        writer.writeheader()
        for i in range(1, args.count + 1):
            username = f"{args.prefix}_{i:03d}"
            password = secrets.token_urlsafe(24)
            payload = {"username": username, "password": password}
            for attempt in range(4):
                try:
                    response = requests.post(args.base_url.rstrip("/") + "/auth/register",
                                             json=payload, timeout=25)
                except requests.RequestException as exc:
                    if attempt == 3:
                        sys.exit(f"Registration network failure at user #{i}: {type(exc).__name__}")
                    time.sleep(1.5 * (attempt + 1))
                    continue
                if response.status_code == 201:
                    writer.writerow({"username": username, "password": password})
                    file.flush()
                    break
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                sys.exit(f"Registration stopped at #{i}, HTTP {response.status_code}; "
                         "check logs and retry with NEW prefix, do not overwrite local CSV")
            if i % 10 == 0 or i == args.count:
                print(f"Registered {i}/{args.count}")
            time.sleep(max(0, args.delay))
    print("Done. Do not upload the credentials CSV to GitHub.")


if __name__ == "__main__":
    main()
