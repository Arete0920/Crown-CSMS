"""Behavioral contract for unscored, school-bound and append-only teacher observations."""
import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import AcademicYear, CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from core.permissions import user_has_permission
from hr.models import Employee
from teacher_evaluations.models import (
    TeacherEvaluationAccessEvent,
    TeacherEvaluationAssignment,
    TeacherEvaluationCycle,
    TeacherEvaluationEvent,
    TeacherObservation,
    TeacherObservationResponse,
)

pytestmark = pytest.mark.django_db
BASE = "/api/v1/teacher-evaluations/"


def grant(user, *codes):
    """Create paired generic and person/school-specific grants for synthetic tests."""
    role = f"evaluation-{uuid.uuid4().hex[:12]}"
    UserRole.objects.create(user=user, school=user.school, role_code=role)
    authorizer = UserAccount.objects.create_user(
        username=f"eval-grantor-{uuid.uuid4().hex[:12]}",
        email=f"eval-grantor-{uuid.uuid4().hex}@example.test",
        school=user.school,
    )
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(
            code=code, defaults={"description": "Scoped evaluation test grant"}
        )
        RolePermission.objects.create(role_code=role, permission=permission)
        if code in dict(TeacherEvaluationAccessEvent.CAPABILITIES):
            TeacherEvaluationAccessEvent.objects.create(
                school=user.school, user=user, authorized_by=authorizer,
                permission_code=code, action="grant", reason="Fictional test setup only",
            )
    return role


def client(user, school=None):
    instance = APIClient()
    instance.force_authenticate(user=user)
    return instance


def get(user, school, uri, params=None):
    return client(user).get(uri, data=params or {}, HTTP_X_SCHOOL_ID=str(school.pk))


def post(user, school, uri, payload):
    return client(user).post(uri, payload, format="json", HTTP_X_SCHOOL_ID=str(school.pk))


def key():
    return str(uuid.uuid4())


@pytest.fixture
def scenario(settings):
    # Full-suite tests/conftest disables this globally; confidential APIs must opt in.
    settings.TENANT_HEADER_REQUIRED = True
    school = School.objects.create(name="Teacher Evaluation Fictional One", timezone="UTC")
    other = School.objects.create(name="Teacher Evaluation Fictional Two", timezone="UTC")
    today = timezone.now().date()
    year = AcademicYear.objects.create(
        school=school, name="Fictional Evaluation Year",
        start_date=today - timedelta(days=90), end_date=today + timedelta(days=90)
    )
    staff = Staff.objects.create(
        school=school, first_name="Grace", last_name="Sample",
        email="grace-eval@example.test", role_type="TEACHER"
    )
    unrelated_staff = Staff.objects.create(
        school=school, first_name="Other", last_name="Sample",
        email="other-eval@example.test", role_type="TEACHER"
    )
    staff_other = Staff.objects.create(
        school=other, first_name="Cross", last_name="School",
        email="cross-eval@example.test", role_type="TEACHER"
    )
    def user(label, school_id=school, linked=None):
        u = UserAccount.objects.create_user(
            username=f"teacher-eval-{label}-{uuid.uuid4().hex[:6]}",
            email=f"teacher-eval-{label}-{uuid.uuid4().hex[:6]}@example.test",
            school=school_id,
        )
        if linked is not None:
            u.staff = linked
            u.save(update_fields=["staff"])
        return u
    admin = user("admin")
    evaluator = user("evaluator")
    teacher = user("subject", linked=staff)
    unrelated = user("unrelated", linked=unrelated_staff)
    outsider = user("outsider", school_id=other, linked=staff_other)
    hr = user("hr")
    grant(admin, "evaluation.assign")
    grant(evaluator, "evaluation.observe", "evaluation.read_assigned")
    grant(teacher, "evaluation.read_self", "evaluation.respond_self")
    grant(unrelated, "evaluation.read_self", "evaluation.respond_self")
    grant(outsider, "evaluation.read_self", "evaluation.respond_self")
    grant(hr, "hr.view", "hr.edit", "pd.view", "classroom.view")
    return {
        "school": school, "other": other, "year": year, "staff": staff,
        "unrelated_staff": unrelated_staff, "staff_other": staff_other,
        "admin": admin, "evaluator": evaluator, "teacher": teacher,
        "unrelated": unrelated, "outsider": outsider, "hr": hr,
    }


def create_cycle(s, **overrides):
    payload = {
        "request_key": key(),
        "staff_id": str(s["staff"].pk),
        "academic_year_id": str(s["year"].pk),
        "evaluator_id": str(s["evaluator"].pk),
        "title": "Instructional practice: unscored annual observation",
        **overrides,
    }
    return post(s["admin"], s["school"], BASE + "cycles/", payload)


def create_observation(s, cycle_id, **overrides):
    return post(s["evaluator"], s["school"], BASE + f"cycles/{cycle_id}/observations/", {
        "request_key": key(),
        "observed_at": timezone.now().isoformat(),
        "narrative": "Observed an explicit lesson objective and an evidence-based learning check.",
        **overrides,
    })


def submit(s, observation_id, **overrides):
    return post(s["evaluator"], s["school"], BASE + f"observations/{observation_id}/submit/", {
        "request_key": key(), "version": 1, **overrides
    })


def respond(s, observation_id, **overrides):
    return post(s["teacher"], s["school"], BASE + f"observations/{observation_id}/responses/", {
        "request_key": key(), "choice": "acknowledged_receipt", "comment": "", **overrides
    })


def test_full_persisted_cycle_and_immutable_history(scenario):
    s = scenario
    created = create_cycle(s)
    assert created.status_code == 201
    cycle_id = created.data["id"]
    assert TeacherEvaluationAssignment.objects.get(cycle_id=cycle_id).evaluator == s["evaluator"]
    assert get(s["teacher"], s["school"], BASE + "cycles/").data["total"] == 1
    observation = create_observation(s, cycle_id)
    assert observation.status_code == 201
    obs_id = observation.data["id"]
    own_draft = get(s["teacher"], s["school"], BASE + f"cycles/{cycle_id}/")
    assert own_draft.status_code == 200
    assert own_draft.data["observations"] == []
    assert get(s["evaluator"], s["school"], BASE + f"cycles/{cycle_id}/").data["observations"][0]["status"] == "draft"
    sent = submit(s, obs_id)
    assert sent.status_code == 200 and sent.data["status"] == "submitted" and sent.data["version"] == 2
    received = respond(s, obs_id)
    assert received.status_code == 201 and received.data["choice"] == "acknowledged_receipt"
    readback = get(s["teacher"], s["school"], BASE + f"cycles/{cycle_id}/")
    assert readback.status_code == 200
    assert "no-store" in readback["Cache-Control"]
    assert "private" in readback["Cache-Control"]
    item = readback.data["observations"][0]
    assert item["narrative"] == observation.data["narrative"]
    assert item["teacher_response"]["choice"] == "acknowledged_receipt"
    assert TeacherEvaluationEvent.objects.filter(cycle_id=cycle_id).count() == 4
    assert all("narrative" not in e.after for e in TeacherEvaluationEvent.objects.all())
    assert not Employee.objects.exists()


def test_unauthorized_hr_unassigned_and_outsider_cannot_read_or_mutate(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    obs = create_observation(s, cycle).data["id"]
    assert get(s["hr"], s["school"], BASE + "cycles/").status_code == 403
    assert get(s["hr"], s["school"], BASE + f"cycles/{cycle}/").status_code == 404
    assert get(s["unrelated"], s["school"], BASE + "cycles/").data["total"] == 0
    assert get(s["unrelated"], s["school"], BASE + f"cycles/{cycle}/").status_code == 404
    assert get(s["outsider"], s["other"], BASE + f"cycles/{cycle}/").status_code == 404
    assert get(s["outsider"], s["other"], BASE + "cycles/").data["total"] == 0
    assert post(s["unrelated"], s["school"], BASE + f"observations/{obs}/responses/", {
        "request_key": key(), "choice": "disputed", "comment": "Unauthorized"
    }).status_code == 404
    assert post(s["teacher"], s["school"], BASE + f"observations/{obs}/responses/", {
        "request_key": key(), "choice": "acknowledged_receipt", "comment": ""
    }).status_code == 404  # draft never reachable for teacher response
    assert TeacherObservationResponse.objects.count() == 0
    assert TeacherEvaluationEvent.objects.count() == 2


def test_cross_school_write_and_forged_tenant_are_denied(scenario):
    s = scenario
    foreign = create_cycle(s, staff_id=str(s["staff_other"].pk))
    assert foreign.status_code == 404
    assert TeacherEvaluationCycle.objects.count() == 0
    fake = client(s["admin"]).post(BASE + "cycles/", {
        "request_key": key(), "staff_id": str(s["staff"].pk),
        "academic_year_id": str(s["year"].pk), "evaluator_id": str(s["evaluator"].pk),
        "title": "Untrusted"
    }, format="json", HTTP_X_SCHOOL_ID=str(s["other"].pk))
    assert fake.status_code in (403, 404)
    assert TeacherEvaluationEvent.objects.count() == 0


def test_missing_header_and_default_role_grants_fail_closed(scenario):
    s = scenario
    assert client(s["admin"]).get(BASE + "cycles/").status_code == 400
    assert client(s["teacher"]).get(BASE + "cycles/").status_code == 400
    assert get(s["admin"], s["school"], BASE + "cycles/").status_code == 403
    assert post(s["hr"], s["school"], BASE + "cycles/", {
        "request_key": key(), "staff_id": str(s["staff"].pk),
        "academic_year_id": str(s["year"].pk), "evaluator_id": str(s["evaluator"].pk),
        "title": "Forbidden"
    }).status_code == 403


def test_idempotent_cycle_conflict_and_immutable_records(scenario):
    s = scenario
    request_key = key()
    created = create_cycle(s, request_key=request_key)
    assert created.status_code == 201
    assert create_cycle(s, request_key=request_key).status_code == 200
    assert create_cycle(s, request_key=request_key, title="Changed").status_code == 409
    assert create_cycle(s).status_code == 409
    assert TeacherEvaluationCycle.objects.count() == 1
    assert TeacherEvaluationEvent.objects.count() == 1
    event = TeacherEvaluationEvent.objects.get()
    with pytest.raises(DjangoValidationError):
        event.save()
    with pytest.raises(DjangoValidationError):
        event.delete()
    with pytest.raises(DjangoValidationError):
        TeacherEvaluationEvent.objects.all().update(action="rewritten")
    with pytest.raises(DjangoValidationError):
        TeacherEvaluationCycle.objects.all().delete()


def test_observation_and_response_idempotency_stale_versions_and_mutation_guards(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    idem = key()
    recorded_time = timezone.now().isoformat()
    obs = create_observation(s, cycle, request_key=idem, observed_at=recorded_time)
    assert obs.status_code == 201
    oid = obs.data["id"]
    replayed = create_observation(s, cycle, request_key=idem, observed_at=recorded_time)
    assert replayed.status_code == 200
    assert replayed.data["id"] == oid
    assert replayed.data["narrative"] == obs.data["narrative"]
    assert create_observation(s, cycle, request_key=idem, observed_at=recorded_time, narrative="Changed").status_code == 409
    submit_idem = key()
    assert submit(s, oid, request_key=submit_idem).status_code == 200
    assert submit(s, oid, request_key=submit_idem).status_code == 200
    assert submit(s, oid).status_code == 409
    assert submit(s, oid, version=True).status_code == 400
    rkey = key()
    first_response = respond(s, oid, request_key=rkey, choice="disputed", comment="I disagree with the observation.")
    replay_response = respond(s, oid, request_key=rkey, choice="disputed", comment="I disagree with the observation.")
    assert first_response.status_code == 201
    assert replay_response.status_code == 200
    assert replay_response.data == first_response.data
    assert "I disagree with the observation." not in str(TeacherEvaluationEvent.objects.get(action="teacher_response").after)
    assert respond(s, oid, choice="acknowledged_receipt").status_code == 409
    row = TeacherObservation.objects.get(pk=oid)
    row.narrative = "Rewritten"
    with pytest.raises(DjangoValidationError):
        row.save()
    with pytest.raises(DjangoValidationError):
        TeacherObservation.objects.filter(pk=oid).update(status="draft")
    with pytest.raises(DjangoValidationError):
        TeacherObservationResponse.objects.get().delete()
    assert TeacherEvaluationEvent.objects.filter(cycle_id=cycle).count() == 4


def test_permission_revocation_blocks_existing_evaluator_and_teacher(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    obs = create_observation(s, cycle).data["id"]
    RolePermission.objects.filter(
        role_code__in=s["evaluator"].roles.values_list("role_code", flat=True),
        permission__code="evaluation.observe"
    ).delete()
    assert create_observation(s, cycle).status_code == 404
    assert submit(s, obs).status_code == 404
    assert TeacherObservation.objects.get(pk=obs).status == "draft"
    RolePermission.objects.filter(
        role_code__in=s["teacher"].roles.values_list("role_code", flat=True),
        permission__code="evaluation.read_self"
    ).delete()
    assert get(s["teacher"], s["school"], BASE + f"cycles/{cycle}/").status_code == 404


def test_no_self_review_and_rejects_wrong_actor_or_year(scenario):
    s = scenario
    # UserAccount.staff is one-to-one; use a separate canonical staff target
    # instead of assigning the already-linked subject to a second account.
    self_staff = Staff.objects.create(
        school=s["school"], first_name="Self", last_name="Review",
        email=f"self-{uuid.uuid4().hex}@example.test", role_type="TEACHER",
    )
    s["admin"].staff = self_staff
    s["admin"].save(update_fields=["staff"])
    assert create_cycle(s, staff_id=str(self_staff.pk)).status_code == 403
    s["admin"].staff = None
    s["admin"].save(update_fields=["staff"])
    assert create_cycle(s, evaluator_id=str(s["teacher"].pk)).status_code == 403
    assert create_cycle(s, title="").status_code == 400
    assert create_cycle(s, title="A" * 161).status_code == 400
    s["staff"].status = "INACTIVE"
    s["staff"].save(update_fields=["status"])
    assert create_cycle(s).status_code == 404
    assert TeacherEvaluationCycle.objects.count() == 0


def test_dispute_requires_text_and_observation_year_is_checked(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    old_date = (timezone.now() - timedelta(days=366)).isoformat()
    assert create_observation(s, cycle, observed_at=old_date).status_code == 400
    obs = create_observation(s, cycle).data["id"]
    assert submit(s, obs).status_code == 200
    assert respond(s, obs, choice="disputed", comment="").status_code == 400
    assert TeacherObservationResponse.objects.count() == 0
    assert respond(s, obs, choice="disputed", comment="Please review the documented lesson context.").status_code == 201
    assert TeacherEvaluationEvent.objects.filter(cycle_id=cycle).count() == 4


def test_failed_validation_has_no_partial_mutation(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    assert create_observation(s, cycle, narrative="").status_code == 400
    assert create_observation(s, cycle, observed_at="not-a-date").status_code == 400
    assert TeacherObservation.objects.count() == 0
    assert TeacherEvaluationEvent.objects.count() == 1


def test_cycle_detail_paginates_authorized_observations_without_draft_leakage(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    base = timezone.now()
    submitted = []
    for index in range(101):
        submitted.append(TeacherObservation.objects.create(
            school=s["school"], cycle_id=cycle, evaluator=s["evaluator"],
            observed_at=base - timedelta(minutes=index + 1),
            narrative=f"Fictional submitted observation {index}",
            status="submitted", submitted_at=base,
        ))
    oldest = submitted[-1]
    TeacherObservationResponse.objects.create(
        school=s["school"], observation=oldest, teacher=s["teacher"],
        choice="disputed", comment="Please correct the documented context.",
    )
    draft = TeacherObservation.objects.create(
        school=s["school"], cycle_id=cycle, evaluator=s["evaluator"],
        observed_at=base, narrative="Confidential evaluator-only draft",
    )
    route = BASE + f"cycles/{cycle}/"

    evaluator_first = get(s["evaluator"], s["school"], route)
    assert evaluator_first.status_code == 200
    assert evaluator_first.data["observations_total"] == 102
    assert evaluator_first.data["observations_next_offset"] == 100
    assert len(evaluator_first.data["observations"]) == 100
    assert str(draft.pk) in {item["id"] for item in evaluator_first.data["observations"]}
    evaluator_second = get(s["evaluator"], s["school"], route, {"offset": "100"})
    assert evaluator_second.status_code == 200
    assert len(evaluator_second.data["observations"]) == 2
    assert evaluator_second.data["observations_next_offset"] is None
    assert str(oldest.pk) in {item["id"] for item in evaluator_second.data["observations"]}

    teacher_first = get(s["teacher"], s["school"], route)
    assert teacher_first.status_code == 200
    assert teacher_first.data["observations_total"] == 101
    assert teacher_first.data["observations_next_offset"] == 100
    assert len(teacher_first.data["observations"]) == 100
    assert all(item["status"] == "submitted" for item in teacher_first.data["observations"])
    teacher_second = get(s["teacher"], s["school"], route, {"offset": "100"})
    assert teacher_second.status_code == 200
    assert teacher_second.data["observations_total"] == 101
    assert teacher_second.data["observations_next_offset"] is None
    assert len(teacher_second.data["observations"]) == 1
    assert teacher_second.data["observations"][0]["id"] == str(oldest.pk)
    assert teacher_second.data["observations"][0]["teacher_response"]["choice"] == "disputed"
    assert str(draft.pk) not in {
        item["id"] for item in (
            teacher_first.data["observations"] + teacher_second.data["observations"]
        )
    }
    assert "no-store" in teacher_second["Cache-Control"]
    assert "private" in teacher_second["Cache-Control"]

    assert get(s["teacher"], s["school"], route, {"offset": "-1"}).status_code == 400
    assert get(s["teacher"], s["school"], route, {"offset": "garbled"}).status_code == 400
    assert get(s["teacher"], s["school"], route, {"offset": "100001"}).status_code == 400
    assert get(s["unrelated"], s["school"], route, {"offset": "100"}).status_code == 404
    assert get(s["outsider"], s["other"], route, {"offset": "100"}).status_code == 404
    assert get(s["hr"], s["school"], route, {"offset": "100"}).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_observation_retry_commits_one_event(scenario):
    """Two real DB connections sharing a retry key must persist one observation."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock and retry proof requires PostgreSQL.")
    s = scenario
    cycle_id = create_cycle(s).data["id"]
    idem = key()
    observed_at = timezone.now().isoformat()
    barrier = Barrier(2)

    def worker():
        connections.close_all()
        try:
            barrier.wait(timeout=15)
            result = post(s["evaluator"], s["school"], BASE + f"cycles/{cycle_id}/observations/", {
                "request_key": idem,
                "observed_at": observed_at,
                "narrative": "Observed an independently verifiable classroom practice.",
            })
            return result.status_code, result.data
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        responses = [future.result(timeout=30) for future in futures]
    assert sorted(code for code, _ in responses) == [200, 201]
    assert responses[0][1]["id"] == responses[1][1]["id"]
    assert responses[0][1]["narrative"] == responses[1][1]["narrative"]
    assert TeacherObservation.objects.filter(cycle_id=cycle_id).count() == 1
    assert TeacherEvaluationEvent.objects.filter(
        cycle_id=cycle_id, action="observation_draft"
    ).count() == 1

def test_shared_role_code_does_not_transfer_evaluation_authority_to_another_school(scenario):
    s = scenario
    code = "evaluation.assign"
    p, _ = CrownPermission.objects.get_or_create(code=code)
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=p)
    UserRole.objects.create(user=s["admin"], school=s["school"], role_code="HEAD_OF_SCHOOL")
    foreign_head = UserAccount.objects.create_user(
        username=f"foreign-head-{uuid.uuid4().hex[:12]}", school=s["other"],
    )
    UserRole.objects.create(user=foreign_head, school=s["other"], role_code="HEAD_OF_SCHOOL")
    assert user_has_permission(s["admin"], code, school=s["school"])
    assert user_has_permission(foreign_head, code, school=s["other"])
    assert post(foreign_head, s["other"], BASE + "cycles/", {
        "request_key": key(), "staff_id": str(s["staff_other"].pk),
        "academic_year_id": str(s["year"].pk),
        "evaluator_id": str(s["evaluator"].pk), "title": "Forbidden",
    }).status_code == 403
    assert get(foreign_head, s["other"], BASE + "cycles/").status_code == 403
    assert create_cycle(s).status_code == 201
    assert TeacherEvaluationCycle.objects.count() == 1


def test_school_user_specific_revoke_overrides_unchanged_role_grants(scenario):
    s = scenario
    cycle = create_cycle(s).data["id"]
    observation = create_observation(s, cycle).data["id"]
    assert user_has_permission(s["evaluator"], "evaluation.observe", school=s["school"])
    TeacherEvaluationAccessEvent.objects.create(
        school=s["school"], user=s["evaluator"], authorized_by=s["admin"],
        permission_code="evaluation.observe", action="revoke",
        reason="Fictional access reassignment",
    )
    assert user_has_permission(s["evaluator"], "evaluation.observe", school=s["school"])
    assert create_observation(s, cycle).status_code == 404
    assert submit(s, observation).status_code == 404
    assert TeacherObservation.objects.get(pk=observation).status == "draft"
    TeacherEvaluationAccessEvent.objects.create(
        school=s["school"], user=s["teacher"], authorized_by=s["admin"],
        permission_code="evaluation.read_self", action="revoke",
        reason="Fictional access suspension",
    )
    assert get(s["teacher"], s["school"], BASE + f"cycles/{cycle}/").status_code == 404
    assert get(s["teacher"], s["school"], BASE + "cycles/").status_code == 403
    TeacherEvaluationAccessEvent.objects.create(
        school=s["school"], user=s["evaluator"], authorized_by=s["admin"],
        permission_code="evaluation.observe", action="grant",
        reason="Fictional access reinstatement",
    )
    assert create_observation(s, cycle).status_code == 201

def test_access_event_rejects_cross_school_and_is_append_only(scenario):
    s = scenario
    with pytest.raises(DjangoValidationError):
        TeacherEvaluationAccessEvent.objects.create(
            school=s["school"], user=s["outsider"], authorized_by=s["admin"],
            permission_code="evaluation.assign", action="grant", reason="Forbidden",
        )
    event = TeacherEvaluationAccessEvent.objects.filter(user=s["admin"]).first()
    with pytest.raises(DjangoValidationError):
        event.save()
    with pytest.raises(DjangoValidationError):
        event.delete()


def test_access_decision_timestamp_and_uuid_tie_cannot_restore_old_grant(scenario):
    """The newest committed version wins even if UUID order is reversed."""
    from unittest.mock import patch

    s = scenario
    cycle = create_cycle(s).data["id"]
    moment = timezone.now()
    with patch("django.db.models.fields.timezone.now", return_value=moment):
        granted = TeacherEvaluationAccessEvent.objects.create(
            id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            school=s["school"], user=s["evaluator"], authorized_by=s["admin"],
            permission_code="evaluation.observe", action="grant",
            reason="Synthetic fixed-time access test",
        )
        revoked = TeacherEvaluationAccessEvent.objects.create(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            school=s["school"], user=s["evaluator"], authorized_by=s["admin"],
            permission_code="evaluation.observe", action="revoke",
            reason="Synthetic later revocation",
        )
    assert granted.created_at == revoked.created_at
    assert revoked.decision_version == granted.decision_version + 1
    assert create_observation(s, cycle).status_code == 404
    assert TeacherEvaluationAccessEvent.objects.filter(
        school=s["school"], user=s["evaluator"],
        permission_code="evaluation.observe",
    ).first().action == "revoke"


@pytest.mark.django_db(transaction=True)
def test_postgresql_simultaneous_access_decisions_are_serialized(scenario):
    """Independent PostgreSQL connections must produce unique ordered versions."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("Authorization ordering proof requires PostgreSQL row locks.")

    s = scenario
    cycle = create_cycle(s).data["id"]
    school_id = s["school"].pk
    target_id = s["evaluator"].pk
    grantor_id = s["admin"].pk
    last_before = TeacherEvaluationAccessEvent.objects.filter(
        school_id=school_id, user_id=target_id,
        permission_code="evaluation.observe",
    ).order_by("-decision_version").values_list("decision_version", flat=True).first()
    barrier = Barrier(2)

    def writer(action):
        connections.close_all()
        try:
            barrier.wait(timeout=20)
            entry = TeacherEvaluationAccessEvent.objects.create(
                school_id=school_id, user_id=target_id, authorized_by_id=grantor_id,
                permission_code="evaluation.observe", action=action,
                reason=f"Fictional simultaneous {action}",
            )
            return entry.decision_version, entry.action
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(writer, action) for action in ("grant", "revoke")]
        decisions = [future.result(timeout=45) for future in futures]

    assert sorted(version for version, _ in decisions) == [last_before + 1, last_before + 2]
    final_action = max(decisions)[1]
    latest = TeacherEvaluationAccessEvent.objects.filter(
        school_id=school_id, user_id=target_id,
        permission_code="evaluation.observe",
    ).first()
    assert (latest.decision_version, latest.action) == (last_before + 2, final_action)
    assert create_observation(s, cycle).status_code == (201 if final_action == "grant" else 404)

