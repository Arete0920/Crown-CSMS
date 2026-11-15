"""Normal registrar conversion and real persistence; fictional readiness is seed input."""
from io import StringIO
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from admissions.models import AdmissionsApplication
from applications.models import ApplicationEvent
from core.models import School, Student, Enrollment
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_admissions import prepare_presenter_admissions

pytestmark = pytest.mark.django_db


def test_registrar_enrolls_verified_applicant_once_and_denies_parent_and_foreign_tenant(local_runtime, operator_secrets):
    call_command("seed_permissions", stdout=StringIO())
    prepare_presenter(apply=True, enable_password_login=True)
    assert prepare_presenter_admissions()["mode"] == "PREFLIGHT"
    assert not AdmissionsApplication.objects.exists()
    fixture = prepare_presenter_admissions(apply=True)
    registrar, tokens = login("admissions_director", operator_secrets)
    parent, _ = login("parent", operator_secrets)
    body = {"application_id": fixture["admissions_conversion_legacy_application_id"]}
    path = "/api/admissions/enroll/"
    assert parent.post(path, body, format="json").status_code == 403
    before = AdmissionsApplication.objects.get(pk=body["application_id"])
    assert before.status == "ACCEPTED"
    # Readiness is explicit fictional initial data, with deposit WAIVED. No
    # successful enrollment response is fabricated by the fixture.
    state = ApplicationEvent.objects.get(application_id=fixture["admissions_conversion_canonical_application_id"],
        event_type="enrollment_state_updated")
    assert state.payload["deposit_status"] == "waived" and state.payload["demo_payment_processed"] is False
    created = registrar.post(path, body, format="json")
    assert created.status_code == 200, created.content
    assert created.json()["already_enrolled"] is False
    again = registrar.post(path, body, format="json")
    assert again.status_code == 200 and again.json()["already_enrolled"] is True
    before.refresh_from_db()
    assert before.status == "ENROLLED"
    # This legacy action confirms canonical enrollment; it does not implement
    # the CoreStudent lifecycle activation transition. Record that limitation.
    assert Student.objects.get(pk=fixture["admissions_conversion_student_id"]).status == "APPLICANT"
    assert Enrollment.objects.filter(pk=fixture["admissions_conversion_enrollment_id"], status="ENROLLED").count() == 1
    assert ApplicationEvent.objects.filter(application_id=fixture["admissions_conversion_canonical_application_id"],
        event_type="enrollment_confirmed").count() == 1
    for _ in range(2):
        result = registrar.get("/api/v1/admissions/summary/")
        assert result.status_code == 200, result.content
        assert result.json()["pipeline"]["by_stage"]["enrolled"] >= 1
    foreign = School.objects.create(name="Independent invented admissions school")
    registrar.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert registrar.post(path, body, format="json").status_code == 404
    with pytest.raises(CommandError):
        prepare_presenter_admissions(apply=True)
