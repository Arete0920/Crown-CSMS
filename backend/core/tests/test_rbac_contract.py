import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School, UserRole

pytestmark = pytest.mark.django_db


def _mk_school(name="RBAC Test Academy"):
    return School.objects.create(name=name)


def _mk_user(label):
    # UserAccount extends AbstractUser — username is the auth field, not email.
    User = get_user_model()
    return User.objects.create_user(username=f"{label}-{uuid.uuid4()}", password="Passw0rd!")


def _assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _client_for(user, school_id):
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school_id))
    return c


def _anon_client(school_id=None):
    c = APIClient()
    if school_id:
        c.credentials(HTTP_X_SCHOOL_ID=str(school_id))
    return c


@pytest.fixture
def school():
    return _mk_school()


@pytest.fixture
def users(school):
    # Valid UserRole.role_code values (from core/models.py UserRole.ROLE_CODE_CHOICES):
    # HEAD_OF_SCHOOL, AID_DIRECTOR, FINANCE_DIRECTOR, REGISTRAR, TEACHER, PARENT, STUDENT, SUPPORT
    # ADMIN does not exist — FINANCE_DIRECTOR is the privileged finance-level role.
    u = {
        "FINANCE_DIRECTOR": _mk_user("fin-dir"),
        "HEAD_OF_SCHOOL": _mk_user("hos"),
        "TEACHER": _mk_user("teacher"),
        "PARENT": _mk_user("parent"),
        "STUDENT": _mk_user("student"),
    }
    for role, user in u.items():
        _assign_role(user, school, role)
    return u


def test_requires_auth_for_invariants(school):
    # Unauthed should not be allowed even with tenant header.
    c = _anon_client(school_id=school.id)
    r = c.get("/api/v1/ledger/invariants/")
    assert r.status_code in (401, 403), r.content


def test_requires_tenant_header_for_invariants(users, school):
    # Authed without tenant header should fail fast (tenant enforcement).
    c = APIClient()
    c.force_authenticate(user=users["HEAD_OF_SCHOOL"])
    r = c.get("/api/v1/ledger/invariants/")
    assert r.status_code in (400, 403), r.content


@pytest.mark.parametrize(
    "role,expected",
    [
        ("FINANCE_DIRECTOR", 200),
        ("HEAD_OF_SCHOOL", 200),
        ("TEACHER", 403),
        ("PARENT", 403),
        ("STUDENT", 403),
    ],
)
def test_invariants_role_matrix(users, school, role, expected):
    c = _client_for(users[role], school.id)
    r = c.get("/api/v1/ledger/invariants/")
    assert r.status_code == expected, (role, r.status_code, r.content)
