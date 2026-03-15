"""
backend/onboarding/tests/test_views.py

Covers:
- Auth required / missing school header
- Tenant isolation (cross-school session access denied)
- Upload: missing file, bad extension, downstream state reset
- Validate: valid CSV, missing column, no file
- Commit: requires confirm, blocks on errors, idempotent, PII cleared
- Verify: status transitions once, idempotent, response shape
- CSV parser: row cap enforcement
"""
import io
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import School
from onboarding.models import ImportSession

User = get_user_model()

BASE = "/api/v1/onboarding/imports/"

VALID_CSV = (
    "student_external_id,student_first_name,student_last_name,student_dob,"
    "grade_level,student_status,guardian_external_id,guardian_first_name,"
    "guardian_last_name,guardian_email,guardian_relationship,household_external_id\n"
    "S001,John,Doe,2010-05-12,5,active,G001,Jane,Doe,jane@example.com,mother,H001\n"
    "S002,Alice,Smith,2011-03-22,4,active,G002,Bob,Smith,bob@example.com,father,H002\n"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def school_a(db):
    return School.objects.create(name=f"School A {uuid.uuid4().hex[:6]}")


@pytest.fixture
def school_b(db):
    return School.objects.create(name=f"School B {uuid.uuid4().hex[:6]}")


@pytest.fixture
def user(db):
    return User.objects.create_user(username=f"user_{uuid.uuid4().hex[:6]}", password="pass")


def _authed_client(user, school):
    token = str(RefreshToken.for_user(user).access_token)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school.id))
    return c


@pytest.fixture
def client_a(user, school_a):
    return _authed_client(user, school_a)


@pytest.fixture
def client_b(user, school_b):
    return _authed_client(user, school_b)


def _make_session(school, user=None, status=ImportSession.STATUS_PENDING, raw_csv="",
                  validate_result=None, commit_result=None):
    s = ImportSession.objects.create(school=school, created_by=user, status=status, raw_csv=raw_csv)
    if validate_result is not None:
        s.validate_result = validate_result
        s.save(update_fields=["validate_result"])
    if commit_result is not None:
        s.commit_result = commit_result
        s.save(update_fields=["commit_result"])
    return s


def _csv_file(content: str, name="test.csv"):
    return SimpleUploadedFile(name, content.encode(), content_type="text/csv")


# ---------------------------------------------------------------------------
# 1. Auth / school header
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAuth:
    def test_unauthenticated_create_denied(self, school_a):
        c = APIClient()
        c.credentials(HTTP_X_SCHOOL_ID=str(school_a.id))
        res = c.post(BASE, {"mode": "students_guardians"}, format="json")
        assert res.status_code in (401, 403)

    def test_missing_school_header_denied(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        res = c.post(BASE, {"mode": "students_guardians"}, format="json")
        assert res.status_code in (400, 403)


# ---------------------------------------------------------------------------
# 2. Create session
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateSession:
    def test_creates_session(self, client_a, school_a):
        res = client_a.post(BASE, {"mode": "students_guardians"}, format="json")
        assert res.status_code == 201
        data = res.json()
        assert "import_id" in data
        assert data["mode"] == "students_guardians"
        assert data["status"] == "pending"
        assert ImportSession.objects.filter(pk=data["import_id"], school=school_a).exists()

    def test_invalid_mode_falls_back_to_default(self, client_a):
        res = client_a.post(BASE, {"mode": "invented_mode"}, format="json")
        assert res.status_code == 201
        assert res.json()["mode"] == "students_guardians"


# ---------------------------------------------------------------------------
# 3. Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTenantIsolation:
    def test_cross_school_upload_denied(self, client_b, school_a):
        session = _make_session(school_a)
        f = _csv_file(VALID_CSV)
        res = client_b.post(f"{BASE}{session.id}/upload/", {"file": f}, format="multipart")
        assert res.status_code == 404

    def test_cross_school_validate_denied(self, client_b, school_a):
        session = _make_session(school_a, status=ImportSession.STATUS_UPLOADED, raw_csv=VALID_CSV)
        res = client_b.post(f"{BASE}{session.id}/validate/", {}, format="json")
        assert res.status_code == 404

    def test_cross_school_preview_denied(self, client_b, school_a):
        session = _make_session(school_a, status=ImportSession.STATUS_VALIDATED, raw_csv=VALID_CSV)
        res = client_b.get(f"{BASE}{session.id}/preview/")
        assert res.status_code == 404

    def test_cross_school_commit_denied(self, client_b, school_a):
        session = _make_session(
            school_a, status=ImportSession.STATUS_VALIDATED, raw_csv=VALID_CSV,
            validate_result={"errors": [], "warnings": []},
        )
        res = client_b.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 404

    def test_cross_school_verify_denied(self, client_b, school_a):
        session = _make_session(
            school_a, status=ImportSession.STATUS_COMMITTED,
            commit_result={"students_imported": 0, "guardians_imported": 0,
                           "households_imported": 0, "exceptions_count": 0},
        )
        res = client_b.get(f"{BASE}{session.id}/verify/")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 4. Upload
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUpload:
    def _new_session_id(self, client_a):
        return client_a.post(BASE, {"mode": "students_guardians"}, format="json").json()["import_id"]

    def test_valid_csv_upload(self, client_a, school_a):
        sid = self._new_session_id(client_a)
        f = _csv_file(VALID_CSV)
        res = client_a.post(f"{BASE}{sid}/upload/", {"file": f}, format="multipart")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["rows_total"] == 2
        assert data["students_detected"] == 2

    def test_missing_file_rejected(self, client_a):
        sid = self._new_session_id(client_a)
        res = client_a.post(f"{BASE}{sid}/upload/", {}, format="multipart")
        assert res.status_code == 400

    def test_wrong_extension_rejected(self, client_a):
        sid = self._new_session_id(client_a)
        f = SimpleUploadedFile("data.xlsx", b"col1,col2\nval1,val2", content_type="text/csv")
        res = client_a.post(f"{BASE}{sid}/upload/", {"file": f}, format="multipart")
        assert res.status_code == 400

    def test_reupload_resets_downstream_state(self, client_a, school_a):
        sid = self._new_session_id(client_a)
        session = ImportSession.objects.get(pk=sid)
        session.validate_result = {"errors": [], "warnings": []}
        session.commit_result = {"students_imported": 1}
        session.save()

        f = _csv_file(VALID_CSV)
        res = client_a.post(f"{BASE}{sid}/upload/", {"file": f}, format="multipart")
        assert res.status_code == 200
        session.refresh_from_db()
        assert session.validate_result is None
        assert session.commit_result is None


# ---------------------------------------------------------------------------
# 5. Validate
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestValidate:
    def test_valid_csv_zero_errors(self, client_a, school_a):
        session = _make_session(school_a, status=ImportSession.STATUS_UPLOADED, raw_csv=VALID_CSV)
        res = client_a.post(f"{BASE}{session.id}/validate/", {}, format="json")
        assert res.status_code == 200
        assert res.json()["errors"] == []
        assert res.json()["rows_total"] == 2

    def test_missing_required_column_produces_error(self, client_a, school_a):
        bad_csv = "student_external_id,student_first_name\nS001,John\n"
        session = _make_session(school_a, status=ImportSession.STATUS_UPLOADED, raw_csv=bad_csv)
        res = client_a.post(f"{BASE}{session.id}/validate/", {}, format="json")
        assert res.status_code == 200
        assert len(res.json()["errors"]) > 0

    def test_no_file_upload_rejected(self, client_a, school_a):
        session = _make_session(school_a)
        res = client_a.post(f"{BASE}{session.id}/validate/", {}, format="json")
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# 6. Commit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCommit:
    def _validated_session(self, school_a):
        return _make_session(
            school_a, status=ImportSession.STATUS_VALIDATED, raw_csv=VALID_CSV,
            validate_result={"errors": [], "warnings": []},
        )

    def test_requires_confirm_true(self, client_a, school_a):
        session = self._validated_session(school_a)
        res = client_a.post(f"{BASE}{session.id}/commit/", {"confirm": False}, format="json")
        assert res.status_code == 400

    def test_blocks_when_validation_errors_present(self, client_a, school_a):
        session = _make_session(
            school_a, status=ImportSession.STATUS_VALIDATED, raw_csv=VALID_CSV,
            validate_result={"errors": [{"row": 2, "field": "x", "message": "bad"}], "warnings": []},
        )
        res = client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 400

    def test_successful_commit_response_shape(self, client_a, school_a):
        session = self._validated_session(school_a)
        res = client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert "students_imported" in data
        assert "guardians_imported" in data
        assert "households_imported" in data

    def test_commit_clears_raw_csv_for_pii(self, client_a, school_a):
        session = self._validated_session(school_a)
        client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        session.refresh_from_db()
        assert session.raw_csv == ""

    def test_commit_idempotent_second_call(self, client_a, school_a):
        session = self._validated_session(school_a)
        client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        res2 = client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res2.status_code == 200
        assert "Already committed" in res2.json().get("detail", "")


# ---------------------------------------------------------------------------
# 7. Verify
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVerify:
    def _committed_session(self, school_a):
        return _make_session(
            school_a, status=ImportSession.STATUS_COMMITTED,
            commit_result={"students_imported": 2, "guardians_imported": 2,
                           "households_imported": 2, "exceptions_count": 0},
        )

    def test_verify_advances_status_once(self, client_a, school_a):
        session = self._committed_session(school_a)
        res = client_a.get(f"{BASE}{session.id}/verify/")
        assert res.status_code == 200
        session.refresh_from_db()
        assert session.status == ImportSession.STATUS_VERIFIED

    def test_verify_idempotent_three_calls(self, client_a, school_a):
        session = self._committed_session(school_a)
        for _ in range(3):
            res = client_a.get(f"{BASE}{session.id}/verify/")
            assert res.status_code == 200
        session.refresh_from_db()
        assert session.status == ImportSession.STATUS_VERIFIED

    def test_verify_response_shape(self, client_a, school_a):
        session = self._committed_session(school_a)
        data = client_a.get(f"{BASE}{session.id}/verify/").json()
        for key in ("session_id", "mode", "students_imported", "guardians_imported",
                    "households_imported", "exceptions_count", "checks"):
            assert key in data, f"missing key: {key}"
        assert isinstance(data["checks"], list)
        assert data["students_imported"] == 2


# ---------------------------------------------------------------------------
# 8. Parser limits (unit)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestParserLimits:
    def test_row_cap_produces_error(self):
        from onboarding.views import _parse_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS, MAX_CSV_ROWS
        header = (
            "student_external_id,student_first_name,student_last_name,student_dob,"
            "grade_level,student_status,guardian_external_id,guardian_first_name,"
            "guardian_last_name,guardian_email,guardian_relationship,household_external_id\n"
        )
        row = "S{i},F,L,2010-01-01,5,active,G{i},GF,GL,g{i}@x.com,mother,H{i}\n"
        big_csv = header + "".join(row.format(i=i) for i in range(MAX_CSV_ROWS + 2))
        result = _parse_csv(big_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS)
        cap_errors = [e for e in result["errors"] if "exceeds" in (e.get("message") or "")]
        assert len(cap_errors) == 1

    def test_bad_date_produces_error(self):
        from onboarding.views import _parse_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS
        bad_csv = VALID_CSV.replace("2010-05-12", "12/05/2010")
        result = _parse_csv(bad_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS)
        date_errors = [e for e in result["errors"] if e.get("field") == "student_dob"]
        assert len(date_errors) == 1

    def test_bad_grade_level_produces_error(self):
        from onboarding.views import _parse_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS
        bad_csv = VALID_CSV.replace(",5,active", ",kindergarten,active")
        result = _parse_csv(bad_csv, REQUIRED_HEADERS_STUDENTS_GUARDIANS)
        grade_errors = [e for e in result["errors"] if e.get("field") == "grade_level"]
        assert len(grade_errors) >= 1
