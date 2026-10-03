import json
from datetime import date
from pathlib import Path

import pytest
from rest_framework.test import APIClient

from core.models import AcademicYear, Student, UserAccount
from finance.models import FinanceObligation
from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from sandbox_demo.services import seed_heritage_flagship, seed_local_heritage_relationships


def test_heritage_manifest_matches_backend_school_and_personas():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "sandbox/seed_packs/school/heritage_core/manifest.json").read_text())
    assert manifest["school"]["enrollment"] == SANDBOX_SCHOOLS["heritage-core"].enrollment
    for persona in manifest["personas"]:
        assert persona["email"] == SANDBOX_PERSONAS[persona["key"]].email
        assert persona["route"] == SANDBOX_PERSONAS[persona["key"]].route


@pytest.mark.django_db
def test_seeded_students_have_grade_appropriate_ages_and_school_year_installments():
    seed_heritage_flagship(reset=True)
    school_id = SANDBOX_SCHOOLS["heritage-core"].id
    year = AcademicYear.objects.get(school_id=school_id, name="2026-2027")
    students = Student.objects.filter(school_id=school_id).select_related("current_grade_level")
    assert students.count() == 700
    for student in students:
        code = student.current_grade_level.code
        expected_age = 4 if code == "PK" else 5 if code == "K" else int(code) + 5
        age = year.start_date.year - student.dob.year - ((year.start_date.month, year.start_date.day) < (student.dob.month, student.dob.day))
        assert age == expected_age
    dates = list(FinanceObligation.objects.filter(school_id=school_id, reference__startswith="HCA-DEMO-TUITION-").order_by("due_date").values_list("due_date", flat=True))
    assert len(dates) == 12
    assert dates[0] == date(2026, 8, 15)
    assert dates[-1] == date(2027, 7, 15)


@pytest.mark.django_db
def test_role_sessions_authorize_finance_without_granting_parent_or_teacher_access(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    settings.TENANT_HEADER_REQUIRED = True
    for role, expected in (("finance_director", 200), ("parent", 403), ("teacher", 403)):
        client = APIClient()
        response = client.post("/api/v1/sandbox/session/", {"role": role, "school": "heritage-core"}, format="json")
        assert response.status_code == 201
        session = response.json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}", HTTP_X_SCHOOL_ID=session["school_id"])
        assert client.get("/api/v1/billing/invoices/").status_code == expected
        assert client.get("/api/v1/payments/exceptions/").status_code == expected


@pytest.mark.django_db
def test_local_seed_links_real_classroom_relationships_and_preserves_denials(settings):
    settings.DEBUG = True
    settings.CROWN_ENV = "local"
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    seed_local_heritage_relationships()
    from sandbox_demo.finance import apply_demo_payment
    director = UserAccount.objects.get(username=SANDBOX_PERSONAS["finance_director"].email)
    assert apply_demo_payment(director)["reconciliation_status"] == "reconciled"
    for role in ("parent", "student"):
        client = APIClient()
        session = client.post("/api/v1/sandbox/session/", {"role": role, "school": "heritage-core"}, format="json").json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}", HTTP_X_SCHOOL_ID=session["school_id"])
        response = client.get("/api/v1/academics/classroom/workspace/", {"audience": role})
        assert response.status_code == 200
        assert response.json()["students"]
        assert client.get("/api/v1/academics/classroom/workspace/", {"audience": "admin"}).status_code == 403
        assert client.get("/api/v1/billing/invoices/").status_code == 403


@pytest.mark.django_db
def test_student_fixture_does_not_reassign_another_accounts_identity(settings):
    from sandbox_demo.student_self_service import _canonical_schedule_fixture, SandboxStudentError
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    user = UserAccount.objects.get(username=SANDBOX_PERSONAS["student"].email)
    identity = _canonical_schedule_fixture(user)
    other = UserAccount.objects.create_user(username="different-student@heritage.example.org", school=user.school)
    identity.account = other
    identity.save(update_fields=["account"])
    with pytest.raises(SandboxStudentError, match="canonical_student_authority_mismatch"):
        _canonical_schedule_fixture(user)
    identity.refresh_from_db()
    assert identity.account_id == other.id


"""Local launcher isolation, startup, and cleanup contracts."""
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("heritage_launcher", Path(__file__).resolve().parents[2] / "scripts/demo/start_heritage_local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_production_environment_cannot_select_database_or_enable_provider(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(launcher, "STATE", Path(directory)), patch.object(launcher, "source_sha", return_value="a" * 40), patch.dict(os.environ, {
            "DATABASE_URL": "postgres://production/db", "DJANGO_ENV": "production",
            "DJANGO_SECRET_KEY": "production-secret", "AZURE_CLIENT_SECRET": "private",
            "TWILIO_AUTH_TOKEN": "private", "STRIPE_SECRET_KEY": "private", "CROWN_DEMO_MODE": "true",
        }):
            env = launcher.local_environment()
            self.assertEqual(env["DATABASE_URL"], "sqlite:///" + (Path(directory) / "heritage.sqlite3").as_posix())
            self.assertEqual(env["DJANGO_ENV"], "local")
            self.assertEqual(env["CROWN_DEMO_MODE"], "false")
            self.assertEqual(env["TENANT_HEADER_REQUIRED"], "true")
            self.assertNotEqual(env["DJANGO_SECRET_KEY"], "production-secret")
            for key in ("AZURE_CLIENT_SECRET", "TWILIO_AUTH_TOKEN", "STRIPE_SECRET_KEY"):
                self.assertNotIn(key, env)
            self.assertEqual(launcher.local_environment()["DJANGO_SECRET_KEY"], env["DJANGO_SECRET_KEY"])

    def test_refuses_an_occupied_demo_port(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 8000))
            with self.assertRaisesRegex(RuntimeError, "already in use"):
                launcher.available_ports()

    def test_cleanup_terminates_started_process(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        launcher.stop(child)
        self.assertIsNotNone(child.poll())

    def test_readiness_refuses_a_server_that_exited(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        with self.assertRaisesRegex(RuntimeError, "stopped before"):
            launcher.wait_ready("http://localhost:4173/sandbox", child, timeout=1)

    def test_source_bundle_requires_valid_commit_identity(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(launcher, "ROOT", Path(directory)), patch.object(subprocess, "check_output", side_effect=FileNotFoundError):
            marker = Path(directory) / "HERITAGE_SOURCE_COMMIT.txt"
            marker.write_text("a" * 40)
            self.assertEqual(launcher.source_sha(), "a" * 40)
            marker.write_text("unknown")
            with self.assertRaisesRegex(RuntimeError, "invalid"):
                launcher.source_sha()


if __name__ == "__main__":
    unittest.main()
