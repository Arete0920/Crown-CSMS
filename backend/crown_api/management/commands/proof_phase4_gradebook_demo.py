"""
Phase 4 demo-token API proof: parent gradebook endpoint.

Uses real demo token path (/api/dev/token/) and calls
/api/v1/gradebook/students/<uuid>/grades/ over HTTP.

Asserts:
  - Demo token acquired (200)
  - Endpoint returns 200
  - student_id, student_name present
  - student_name == "Alex Demo"
  - courses is a list

Usage:
  python manage.py proof_phase4_gradebook_demo [--verbose] [--base-url URL]
"""
from __future__ import annotations

import json
import os
from urllib import error, request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import School
from households.models import Student

DEMO_SCHOOL_NAME = "Heritage Christian Academy"
DEMO_STUDENT_FIRST = "Alex"
DEMO_STUDENT_LAST = "Demo"


class Command(BaseCommand):
    help = "Phase 4 demo-token API proof: gradebook parent endpoint returns demo payload (Alex Demo)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=os.environ.get("CROWN_BASE_URL", "http://127.0.0.1:8000"),
        )
        parser.add_argument("--verbose", action="store_true", default=False)

    def _req(self, method: str, url: str, headers: dict | None = None, body: dict | None = None):
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        hdrs = {"Accept": "application/json"}
        if headers:
            hdrs.update(headers)
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        req = request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with request.urlopen(req, timeout=15) as resp:
                return resp.status, resp.read().decode("utf-8")
        except error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def _assert(self, condition: bool, msg: str):
        if not condition:
            raise CommandError(f"PHASE4_GRADEBOOK_DEMO_PROOF: FAIL :: {msg}")

    def handle(self, *args, **options):
        base = options["base_url"].rstrip("/")
        verbose = options["verbose"]

        def log(msg):
            if verbose:
                self.stdout.write(msg)

        # Resolve DB objects
        school = School.objects.filter(name=DEMO_SCHOOL_NAME).first()
        self._assert(school is not None, f"School '{DEMO_SCHOOL_NAME}' not found. Run seed_demo_school first.")

        student = Student.objects.filter(
            school_id=school.id,
            first_name=DEMO_STUDENT_FIRST,
            last_name=DEMO_STUDENT_LAST,
        ).first()
        self._assert(
            student is not None,
            "Alex Demo student not found. Run seed_demo_parent_gradebook first.",
        )
        log(f"proof_phase4_gradebook_demo: school_id={school.id} student_id={student.id}")

        # Demo key (has default in settings)
        demo_key = getattr(settings, "CROWN_DEMO_KEY", None) or os.environ.get("CROWN_DEMO_KEY", "")
        self._assert(bool(demo_key), "CROWN_DEMO_KEY is not set.")

        # Step 1: acquire demo token
        auth_url = f"{base}/api/dev/token/"
        st, raw = self._req("POST", auth_url, headers={"X-Demo-Key": demo_key}, body={})
        self._assert(st == 200, f"demo token failed: HTTP {st} :: {raw[:300]}")
        payload = json.loads(raw)
        access = payload.get("access") or payload.get("access_token") or payload.get("token")
        self._assert(bool(access), f"demo token response missing access key: keys={list(payload.keys())}")
        log("proof_phase4_gradebook_demo: demo token acquired")

        # Step 2: call parent grades endpoint
        grades_url = f"{base}/api/v1/gradebook/students/{student.id}/grades/"
        st2, raw2 = self._req(
            "GET",
            grades_url,
            headers={
                "Authorization": f"Bearer {access}",
                "X-School-Id": str(school.id),
            },
        )
        self._assert(st2 == 200, f"gradebook endpoint failed: HTTP {st2} :: {raw2[:300]}")
        out = json.loads(raw2)
        log(f"proof_phase4_gradebook_demo: response keys={list(out.keys())}")

        # Step 3: payload assertions
        for k in ("student_id", "student_name", "courses"):
            self._assert(k in out, f"Missing key '{k}' in response: keys={list(out.keys())}")

        self._assert(
            str(out["student_id"]) == str(student.id),
            f"student_id mismatch: expected {student.id}, got {out['student_id']}",
        )
        self._assert(
            out["student_name"].strip() == f"{DEMO_STUDENT_FIRST} {DEMO_STUDENT_LAST}",
            f"student_name mismatch: expected '{DEMO_STUDENT_FIRST} {DEMO_STUDENT_LAST}', got '{out['student_name']}'",
        )
        self._assert(isinstance(out["courses"], list), "courses must be a list")

        self.stdout.write(
            f"PHASE4_GRADEBOOK_DEMO_PROOF: PASS :: student={out['student_name']} courses={len(out['courses'])}"
        )
