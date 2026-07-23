import pytest
from django.core.exceptions import ValidationError

from applications.models import (
    Applicant,
    Application,
    ApplicationChecklistDocument,
    ApplicationChecklistItem,
    ApplicationEvent,
    EnrollmentContract,
)
from core.models import School
from households.models import Guardian, Household, Student


@pytest.fixture
def tenant_graph(db):
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    household_a = Household.objects.create(school_id=school_a.id, name="Family A")
    household_b = Household.objects.create(school_id=school_b.id, name="Family B")
    student_a = Student.objects.create(
        school_id=school_a.id,
        household=household_a,
        first_name="Alex",
        last_name="A",
    )
    student_b = Student.objects.create(
        school_id=school_b.id,
        household=household_b,
        first_name="Blair",
        last_name="B",
    )
    application_a = Application.objects.create(
        school_id=school_a.id,
        household=household_a,
    )
    application_b = Application.objects.create(
        school_id=school_b.id,
        household=household_b,
    )
    return {
        "school_a": school_a,
        "school_b": school_b,
        "household_a": household_a,
        "household_b": household_b,
        "student_a": student_a,
        "student_b": student_b,
        "application_a": application_a,
        "application_b": application_b,
    }


@pytest.mark.django_db
def test_household_children_accept_same_school_and_reject_cross_school(tenant_graph):
    graph = tenant_graph
    guardian = Guardian.objects.create(
        school_id=graph["school_a"].id,
        household=graph["household_a"],
        first_name="Pat",
        last_name="Guardian",
    )
    assert guardian.pk is not None

    with pytest.raises(ValidationError, match="same school"):
        Guardian.objects.create(
            school_id=graph["school_b"].id,
            household=graph["household_a"],
            first_name="Cross",
            last_name="Tenant",
        )

    with pytest.raises(ValidationError, match="same school"):
        Student.objects.create(
            school_id=graph["school_b"].id,
            household=graph["household_a"],
            first_name="Cross",
            last_name="Student",
        )


@pytest.mark.django_db
def test_household_child_update_cannot_move_across_tenants(tenant_graph):
    graph = tenant_graph
    guardian = Guardian.objects.create(
        school_id=graph["school_a"].id,
        household=graph["household_a"],
        first_name="Pat",
        last_name="Guardian",
    )
    guardian.household = graph["household_b"]

    with pytest.raises(ValidationError, match="same school"):
        guardian.save()

    guardian.refresh_from_db()
    assert guardian.household_id == graph["household_a"].id


@pytest.mark.django_db
def test_application_requires_household_from_same_school(tenant_graph):
    graph = tenant_graph

    with pytest.raises(ValidationError, match="same school"):
        Application.objects.create(
            school_id=graph["school_a"].id,
            household=graph["household_b"],
        )


@pytest.mark.django_db
def test_applicant_requires_application_and_student_from_same_school(tenant_graph):
    graph = tenant_graph
    applicant = Applicant.objects.create(
        school_id=graph["school_a"].id,
        application=graph["application_a"],
        student=graph["student_a"],
        first_name="Alex",
        last_name="A",
    )
    assert applicant.pk is not None

    with pytest.raises(ValidationError, match="same school"):
        Applicant.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_b"],
            first_name="Wrong",
            last_name="Application",
        )

    with pytest.raises(ValidationError, match="same school"):
        Applicant.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_a"],
            student=graph["student_b"],
            first_name="Wrong",
            last_name="Student",
        )


@pytest.mark.django_db
def test_application_event_and_checklist_writers_reject_cross_tenant_parents(
    tenant_graph,
):
    graph = tenant_graph

    with pytest.raises(ValidationError, match="same school"):
        ApplicationEvent.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_b"],
            event_type="submitted",
        )

    with pytest.raises(ValidationError, match="same school"):
        ApplicationChecklistItem.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_b"],
            item_key="records",
            title="Records",
        )

    checklist_item = ApplicationChecklistItem.objects.create(
        school_id=graph["school_a"].id,
        application=graph["application_a"],
        item_key="records",
        title="Records",
    )
    with pytest.raises(ValidationError, match="same school"):
        ApplicationChecklistDocument.objects.create(
            school_id=graph["school_b"].id,
            checklist_item=checklist_item,
            file="admissions/checklist/records.pdf",
        )


@pytest.mark.django_db
def test_enrollment_contract_enforces_application_and_amendment_lineage(tenant_graph):
    graph = tenant_graph
    original = EnrollmentContract.objects.create(
        school_id=graph["school_a"].id,
        application=graph["application_a"],
        version=1,
    )

    amendment = EnrollmentContract.objects.create(
        school_id=graph["school_a"].id,
        application=graph["application_a"],
        version=2,
        amended_from=original,
    )
    assert amendment.pk is not None

    with pytest.raises(ValidationError, match="same school"):
        EnrollmentContract.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_b"],
            version=1,
        )

    other_application_contract = EnrollmentContract.objects.create(
        school_id=graph["school_a"].id,
        application=Application.objects.create(
            school_id=graph["school_a"].id,
            household=graph["household_a"],
        ),
        version=1,
    )
    with pytest.raises(ValidationError, match="same application"):
        EnrollmentContract.objects.create(
            school_id=graph["school_a"].id,
            application=graph["application_a"],
            version=3,
            amended_from=other_application_contract,
        )


@pytest.mark.django_db
def test_admissions_update_cannot_repoint_to_cross_tenant_parent(tenant_graph):
    graph = tenant_graph
    event = ApplicationEvent.objects.create(
        school_id=graph["school_a"].id,
        application=graph["application_a"],
        event_type="created",
    )
    event.application = graph["application_b"]

    with pytest.raises(ValidationError, match="same school"):
        event.save()

    event.refresh_from_db()
    assert event.application_id == graph["application_a"].id
