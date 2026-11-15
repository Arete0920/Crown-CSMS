"""Real DB/API acceptance for the isolated presenter foundation, not five-module certification."""
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from academics.models import Assignment, Section
from core.models import Family, School, Student, UserAccount
from crown_api.jwt_utils import build_access_token
from sandbox_demo.academic_seed import seed_heritage_teacher_academics
from sandbox_demo.egress import sandbox_external_egress_blocked
from sandbox_demo.models import SandboxEvent
from sandbox_demo.services import seed_heritage_flagship
from sandbox_demo.universal_demo import prepare_presenter, require_local_presenter, LOCAL_DB, PROVENANCE
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID, UNIVERSAL_SCHOOL, presenter_username

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("event", [PROVENANCE, "universal_presenter_reset_v1"])
def test_public_telemetry_cannot_forge_operator_provenance(event):
    response = APIClient().post("/api/v1/sandbox/events/", {
        "event": event, "school": str(UNIVERSAL_SCHOOL_ID),
        "guidance": "ops", "persona": "operator",
    }, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == "sandbox_event_reserved"
    assert not SandboxEvent.objects.exists()


@pytest.fixture
def local_runtime(settings, monkeypatch):
    settings.CROWN_ENV = "local"
    settings.DEBUG = True
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_DEMO_MODE = False
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = True
    for key in ("WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "WEBSITE_SITE_NAME", "IDENTITY_ENDPOINT", "AZURE_CLIENT_ID",
                "CROWN_SANDBOX_OUTBOUND_DISABLED",
                "DJANGO_ENV", "AZURE_ENVIRONMENT", "ENVIRONMENT", "APP_ENV"):
        monkeypatch.delenv(key, raising=False)
    # Test runner owns an isolated in-memory SQLite DB. Substitute only its
    # expected pathname, retaining the real vendor/settings/environment guard.
    from django.db import connection
    with patch("sandbox_demo.universal_demo.LOCAL_DB", LOCAL_DB.__class__(str(connection.settings_dict["NAME"]))):
        yield


def _client(key="teacher", school_id=UNIVERSAL_SCHOOL_ID):
    user = UserAccount.objects.get(username=presenter_username(key))
    token = build_access_token(user_id=str(user.pk), email=user.email, role=key,
                               school_id=str(user.school_id), ttl_seconds=300)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school_id))
    return client


def _assignment(metrics, client=None):
    client = client or _client()
    url = f"/api/v1/academics/sections/{metrics['teacher_section_id']}/assignments/"
    response = client.post(url, {"name": "Fictional presenter writing",
        "category_id": metrics["teacher_assignment_category_id"], "points_possible": "20",
        "assigned_date": "2026-08-10", "is_published": True}, format="json")
    return url, response


def test_preflight_is_read_only_and_duplicate_apply_refuses(local_runtime, capsys):
    call_command("prepare_universal_presenter")
    assert 'PRECHECK_ONLY' in capsys.readouterr().out
    assert not School.objects.exists()
    metrics = prepare_presenter(apply=True)
    assert metrics["students"] == Student.objects.filter(school_id=UNIVERSAL_SCHOOL_ID).count() == 703
    assert metrics["release_certified"] is False
    with pytest.raises(CommandError, match="already exists"):
        prepare_presenter(apply=True)
    assert SandboxEvent.objects.filter(event=PROVENANCE).count() == 1
    assert not UserAccount.objects.filter(is_superuser=True).exists()
    assert all(not u.has_usable_password() for u in UserAccount.objects.all())


def test_heritage_is_preserved_and_actual_teacher_save_readback_reset(local_runtime):
    heritage = seed_heritage_flagship()
    seed_heritage_teacher_academics()
    original_ids = set(Student.objects.filter(school_id=heritage["school_id"]).values_list("pk", flat=True))
    metrics = prepare_presenter(apply=True)
    original_section = Section.objects.get(school_id=heritage["school_id"])
    original = Assignment.objects.create(school_id=original_section.school_id,
        section=original_section, category=original_section.assignment_categories.first(),
        name="Original Heritage preserved", points_possible=10)
    old_client = _client()
    url, response = _assignment(metrics, old_client)
    assert response.status_code == 201, response.content
    assignment_id = response.json()["id"]
    assert Assignment.objects.get(pk=assignment_id).school_id == UNIVERSAL_SCHOOL_ID
    changed = _client().patch(f"/api/v1/academics/assignments/{assignment_id}/",
                              {"points_possible": "25"}, format="json")
    assert changed.status_code == 200, changed.content
    # Independent bearer-authenticated request approximates API reload, not a
    # claimed browser reload. No forced authentication bypass.
    reopened = _client().get(url)
    assert reopened.status_code == 200
    assert any(row["id"] == assignment_id and row["points_possible"] == "25.00"
               for row in reopened.json()["assignments"])
    reset = prepare_presenter(apply=True, reset=True)
    assert reset["mode"] == "RESET"
    assert old_client.get(f"/api/v1/academics/sections/{reset['teacher_section_id']}/assignments/").status_code in {401, 403, 404}
    assert not Assignment.objects.filter(pk=assignment_id).exists()
    assert Assignment.objects.filter(pk=original.pk, name="Original Heritage preserved").exists()
    assert set(Student.objects.filter(school_id=heritage["school_id"]).values_list("pk", flat=True)) == original_ids
    assert set(reset["teacher_roster_student_ids"]) == set(metrics["teacher_roster_student_ids"])
    assert _assignment(reset)[1].status_code == 201
    assert prepare_presenter(apply=True, reset=True)["mode"] == "RESET"


def test_wrong_role_foreign_header_and_foreign_section_denied(local_runtime):
    original = seed_heritage_flagship()
    other = seed_heritage_teacher_academics()
    metrics = prepare_presenter(apply=True)
    for client in (_client("parent"), _client(school_id=original["school_id"])):
        response = _assignment(metrics, client)[1]
        assert response.status_code in {401, 403, 404}, response.content
    anonymous = APIClient()
    anonymous.credentials(HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID))
    assert _assignment(metrics, anonymous)[1].status_code in {401, 403}
    response = _assignment(other)[1]
    assert response.status_code in {403, 404}, response.content
    assert not Assignment.objects.exists()


def test_collision_and_failed_seed_roll_back(local_runtime):
    school = School.objects.create(id=UNIVERSAL_SCHOOL_ID, name=UNIVERSAL_SCHOOL.name)
    with pytest.raises(CommandError, match="not an owned"):
        prepare_presenter(apply=True)
    school.delete()
    with patch("sandbox_demo.universal_demo.seed_heritage_teacher_academics", side_effect=RuntimeError("failure")):
        with pytest.raises(RuntimeError):
            prepare_presenter(apply=True)
    assert not School.objects.filter(pk=UNIVERSAL_SCHOOL_ID).exists()
    assert not UserAccount.objects.exists()
    assert not SandboxEvent.objects.exists()


def test_reset_refuses_foreign_cascade_and_rolls_back(local_runtime):
    metrics = prepare_presenter(apply=True)
    school = School.objects.create(name="Other fictional school")
    section = Section.objects.get(pk=metrics["teacher_section_id"], school_id=UNIVERSAL_SCHOOL_ID)
    # Corrupt legacy relation: even a cascade with an own-school root must
    # never erase a foreign-school child. Deliberately bypass model validation.
    from academics.models import Enrollment as AcademicEnrollment
    foreign = AcademicEnrollment.objects.filter(section=section).first()
    # Out-of-band corruption is test-only: runtime model guards correctly
    # prohibit this legacy state. Exercise reset's additional cascade defense.
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("UPDATE enrollment SET school_id = %s WHERE id = %s",
                       [school.pk.hex, foreign.pk.hex])
    with pytest.raises(CommandError, match="foreign cascade"):
        prepare_presenter(apply=True, reset=True)
    assert AcademicEnrollment.objects.filter(pk=foreign.pk).exists()
    assert Student.objects.filter(school_id=UNIVERSAL_SCHOOL_ID).count() == 703
    assert prepare_presenter()["exists"]


def test_reset_requires_existing_provenance_and_explicit_apply(local_runtime):
    with pytest.raises(CommandError):
        prepare_presenter(reset=True)
    prepare_presenter(apply=True)
    with pytest.raises(CommandError):
        prepare_presenter(reset=True)


@pytest.mark.parametrize("name,value", [
    ("CROWN_ENV", "dev"), ("DEBUG", False), ("CROWN_DEMO_MODE", True),
    ("CROWN_SANDBOX_ALLOW_OPEN_SESSION", True), ("CROWN_SANDBOX_OUTBOUND_DISABLED", False),
])
def test_hosted_or_unsafe_configuration_denied_before_query(local_runtime, settings, name, value, django_assert_num_queries):
    setattr(settings, name, value)
    with django_assert_num_queries(0), pytest.raises(CommandError):
        prepare_presenter(apply=True)


def test_wrong_database_and_azure_identity_denied_before_query(local_runtime, monkeypatch, django_assert_num_queries):
    with patch("sandbox_demo.universal_demo.LOCAL_DB", LOCAL_DB), django_assert_num_queries(0), pytest.raises(CommandError):
        require_local_presenter()
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-dev.azurewebsites.net")
    with django_assert_num_queries(0), pytest.raises(CommandError):
        prepare_presenter(apply=True)


def test_egress_quarantine_cannot_be_disabled(local_runtime, settings):
    prepare_presenter(apply=True)
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    assert sandbox_external_egress_blocked(school_id=UNIVERSAL_SCHOOL_ID)
    assert sandbox_external_egress_blocked(sender=UserAccount.objects.get(username=presenter_username("teacher")))


def test_unreviewed_module_refuses_reset_and_preserves_data(local_runtime):
    metrics = prepare_presenter(apply=True)
    url, saved = _assignment(metrics)
    assert saved.status_code == 201
    from academics.models import ClassroomRubric
    teacher = UserAccount.objects.get(username=presenter_username("teacher"))
    rubric = ClassroomRubric.objects.create(school_id=UNIVERSAL_SCHOOL_ID,
                                            title="Immutable evidence", created_by=teacher)
    with pytest.raises(CommandError, match="unreviewed"):
        prepare_presenter(apply=True, reset=True)
    assert ClassroomRubric.objects.filter(pk=rubric.pk).exists()
    assert _client().get(url).json()["assignments"][0]["id"] == saved.json()["id"]


@pytest.mark.parametrize("key", ["CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "AZURE_ENVIRONMENT", "APP_ENV"])
def test_conflicting_process_environment_denied(local_runtime, monkeypatch, key, django_assert_num_queries):
    monkeypatch.setenv(key, "production")
    with django_assert_num_queries(0), pytest.raises(CommandError):
        prepare_presenter(apply=True)


def test_generic_generator_refuses_arbitrary_school_and_presenter_reset(local_runtime):
    from dataclasses import replace
    from uuid import uuid4
    from sandbox_demo.services import seed_fictional_school
    with pytest.raises(RuntimeError, match="unregistered"):
        seed_fictional_school(school_spec=replace(UNIVERSAL_SCHOOL, id=str(uuid4())), personas={})
    assert not School.objects.exists()
    with pytest.raises(RuntimeError, match="controlled presenter reset"):
        seed_fictional_school(school_spec=UNIVERSAL_SCHOOL, personas={}, reset=True)
    assert not School.objects.exists()


def test_failed_reset_rebuild_restores_original_principals_and_work(local_runtime):
    metrics = prepare_presenter(apply=True)
    url, saved = _assignment(metrics)
    assert saved.status_code == 201
    teacher_id = UserAccount.objects.get(username=presenter_username("teacher")).pk
    with patch("sandbox_demo.universal_demo.seed_heritage_teacher_academics", side_effect=RuntimeError("rebuild failed")):
        with pytest.raises(RuntimeError, match="rebuild failed"):
            prepare_presenter(apply=True, reset=True)
    assert UserAccount.objects.get(username=presenter_username("teacher")).pk == teacher_id
    assert _client().get(url).json()["assignments"][0]["id"] == saved.json()["id"]
    assert not SandboxEvent.objects.filter(event="universal_presenter_reset_v1").exists()


def test_generic_presenter_seeder_cannot_bypass_setup_or_disable_existing_logins(local_runtime, monkeypatch):
    """Direct generic reuse must not override the operator's presenter and credentials."""
    from dataclasses import replace
    from core.models import UserRole
    from sandbox_demo.catalog import SANDBOX_PERSONAS
    from sandbox_demo.services import seed_fictional_school

    personas = {
        key: replace(persona, email=presenter_username(key))
        for key, persona in SANDBOX_PERSONAS.items()
    }
    for key in SANDBOX_PERSONAS:
        monkeypatch.setenv(
            f"CROWN_PRESENTER_{key.upper()}_PASSWORD",
            f"OnlyTest!Distinct_secret_for_{key}_9312765",
        )
    with pytest.raises(RuntimeError, match="guarded presenter command"):
        seed_fictional_school(school_spec=UNIVERSAL_SCHOOL, personas=personas)
    assert not School.objects.filter(pk=UNIVERSAL_SCHOOL_ID).exists()

    prepare_presenter(apply=True, enable_password_login=True)
    before_passwords = dict(UserAccount.objects.values_list("pk", "password"))
    before_roles = set(UserRole.objects.values_list("school_id", "user_id", "role_code"))
    before_students = set(Student.objects.values_list("pk", "student_number"))
    before_events = set(SandboxEvent.objects.values_list("pk", "event"))

    with pytest.raises(RuntimeError, match="Presenter already exists"):
        seed_fictional_school(school_spec=UNIVERSAL_SCHOOL, personas=personas)

    assert dict(UserAccount.objects.values_list("pk", "password")) == before_passwords
    assert set(UserRole.objects.values_list("school_id", "user_id", "role_code")) == before_roles
    assert set(Student.objects.values_list("pk", "student_number")) == before_students
    assert set(SandboxEvent.objects.values_list("pk", "event")) == before_events
    role = "teacher"
    user = UserAccount.objects.get(username=presenter_username(role))
    password = f"OnlyTest!Distinct_secret_for_{role}_9312765"
    assert user.check_password(password)
    response = APIClient().post("/api/v1/auth/token/", {
        "username": user.username, "password": password,
    }, format="json")
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_owned_presenter_reader_avoids_autocommit_for_update(local_runtime):
    """PostgreSQL rejects FOR UPDATE in autocommit; normal presenter reads cannot request it."""
    from django.db import connection, transaction
    from sandbox_demo.universal_demo import _owned_school

    prepare_presenter(apply=True)
    assert connection.in_atomic_block is False
    with patch.object(School.objects, "select_for_update", side_effect=AssertionError("FOR UPDATE on autocommit read")):
        assert _owned_school().pk == UNIVERSAL_SCHOOL_ID

    # Mutation callers still request the protected row lock inside atomic.
    with transaction.atomic():
        with patch.object(School.objects, "select_for_update", wraps=School.objects.select_for_update) as locked:
            assert _owned_school().pk == UNIVERSAL_SCHOOL_ID
            assert locked.call_count == 1
