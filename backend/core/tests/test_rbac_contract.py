import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School, UserRole

pytestmark = pytest.mark.django_db


def _mk_school(name="RBAC Test Academy"):
    return School.objects.create(name=name)


def _mk_user(label, school):
    # UserAccount extends AbstractUser; username is the auth field, not email.
    # Bind the principal to the canonical school so a matching tenant header is
    # treated as principal context rather than a cross-school override request.
    # Email is unique within a school, so every fixture principal needs its own
    # deterministic identity value rather than the model's shared blank default.
    User = get_user_model()
    token = uuid.uuid4().hex
    return User.objects.create_user(
        username=f"{label}-{token}",
        email=f"{label}-{token}@example.test",
        password="Passw0rd!",
        school=school,
    )


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
    # ADMIN does not exist; FINANCE_DIRECTOR is the privileged finance-level role.
    u = {
        "FINANCE_DIRECTOR": _mk_user("fin-dir", school),
        "HEAD_OF_SCHOOL": _mk_user("hos", school),
        "TEACHER": _mk_user("teacher", school),
        "PARENT": _mk_user("parent", school),
        "STUDENT": _mk_user("student", school),
    }
    for role, user in u.items():
        _assign_role(user, school, role)
    return u


def test_requires_auth_for_invariants(school):
    # Unauthenticated requests are not allowed even with a tenant header.
    c = _anon_client(school_id=school.id)
    r = c.get("/api/v1/ledger/invariants/")
    assert r.status_code in (401, 403), r.content


def test_principal_school_context_without_header(users):
    # Session authentication exposes the principal to Django middleware, which
    # resolves the canonical school without a redundant tenant header.
    c = APIClient()
    c.force_login(users["HEAD_OF_SCHOOL"])
    r = c.get("/api/v1/ledger/invariants/")
    assert r.status_code == 200, r.content


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
