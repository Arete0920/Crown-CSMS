"""School-bound confidentiality for campus operations, with synthetic fixtures."""

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from facops.models import SafetyIncident, VisitorLog, WorkOrder, WorkOrderComment

pytestmark = pytest.mark.django_db


@pytest.fixture
def school_context():
    school = School.objects.create(name="Synthetic Campus Read A")
    foreign = School.objects.create(name="Synthetic Campus Read B")

    def member(label, *, staff=False):
        suffix = uuid.uuid4().hex[:12]
        return UserAccount.objects.create_user(
            username=f"{label}-{suffix}",
            email=f"{label}-{suffix}@example.invalid",
            school=school, is_staff=staff,
        )

    reporter = member("reporter")
    unrelated = member("unrelated-staff", staff=True)
    safety = member("safety-staff", staff=True)
    facilities = member("facilities-staff", staff=True)
    viewer = member("safety-viewer")

    def grant(user, code, role):
        UserRole.objects.create(user=user, school=school, role_code=role)
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(
            role_code=role, permission=permission,
        )

    grant(safety, "safety.edit", "safety_manager")
    grant(facilities, "facilities.edit", "facilities_manager")
    grant(viewer, "safety.view", "safety_viewer")
    SafetyIncident.objects.create(
        school=school, title="Confidential synthetic incident",
    )
    VisitorLog.objects.create(
        school=school, name="Confidential synthetic visitor",
    )
    own_order = WorkOrder.objects.create(
        school=school, title="Own maintenance request", requested_by=reporter,
    )
    other_order = WorkOrder.objects.create(
        school=school, title="Other maintenance request", requested_by=unrelated,
    )
    WorkOrderComment.objects.create(
        school=foreign, work_order=own_order, body="FOREIGN-SCHOOL-PRIVATE-COMMENT",
    )
    foreign_author = UserAccount.objects.create_user(
        username=f"foreign-author-{uuid.uuid4().hex[:12]}",
        email=f"foreign-author-{uuid.uuid4().hex[:12]}@example.invalid",
        school=foreign,
    )
    WorkOrderComment.objects.create(
        school=school, work_order=own_order, author=foreign_author,
        body="Local comment with foreign author",
    )
    WorkOrderComment.objects.create(
        school=school, work_order=own_order, author=reporter,
        body="Local comment with local author",
    )
    return locals()


def request_client(user, school):
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.pk), HTTP_X_ROLE="admin")
    return c


@pytest.mark.parametrize("path", [
    "/api/security/incidents/",
    "/api/security/visitor-logs/",
    "/api/security/alerts/",
    "/api/security/summary/",
])
def test_school_membership_or_staff_bit_cannot_read_private_safety(school_context, path):
    f = school_context
    for user in (f["reporter"], f["unrelated"]):
        response = request_client(user, f["school"]).get(path)
        assert response.status_code == 403, (path, response.status_code)
        assert "Confidential synthetic" not in str(response.content)
    for user in (f["safety"], f["viewer"]):
        response = request_client(user, f["school"]).get(path)
        assert response.status_code == 200, (path, response.status_code)


def test_safety_view_duty_does_not_allow_incident_write(school_context):
    f = school_context
    response = request_client(f["viewer"], f["school"]).post(
        "/api/security/incidents/", {"title": "Denied viewer write"},
        format="json",
    )
    assert response.status_code == 403
    assert not SafetyIncident.objects.filter(title="Denied viewer write").exists()


def test_reporter_cannot_read_others_work_orders_or_cross_school_notes(school_context):
    f = school_context
    c = request_client(f["reporter"], f["school"])
    response = c.get("/api/facilities/work-orders/")
    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == [f["own_order"].pk]
    assert "Other maintenance request" not in str(response.content)
    assert "FOREIGN-SCHOOL-PRIVATE-COMMENT" not in str(response.content)
    forbidden = c.get(f"/api/facilities/work-orders/{f['other_order'].pk}/")
    assert forbidden.status_code == 404
    detail = c.get(f"/api/facilities/work-orders/{f['own_order'].pk}/")
    assert detail.status_code == 200
    assert "FOREIGN-SCHOOL-PRIVATE-COMMENT" not in str(detail.content)


def test_facilities_grant_sees_school_work_orders_only(school_context):
    f = school_context
    response = request_client(f["facilities"], f["school"]).get(
        "/api/facilities/work-orders/"
    )
    assert response.status_code == 200
    assert {r["id"] for r in response.json()} == {
        f["own_order"].pk, f["other_order"].pk,
    }
    assert "FOREIGN-SCHOOL-PRIVATE-COMMENT" not in str(response.content)


def test_foreign_school_selection_does_not_grant_safety_read(school_context):
    f = school_context
    response = request_client(f["safety"], f["foreign"]).get(
        "/api/security/incidents/"
    )
    assert response.status_code in (403, 404)


def test_nested_comment_author_identity_never_crosses_school(school_context):
    # Dirty imported author relationships must not expose another school's user.
    f = school_context
    response = request_client(f["reporter"], f["school"]).get(
        f"/api/facilities/work-orders/{f['own_order'].pk}/"
    )
    assert response.status_code == 200
    comments = {item["body"]: item for item in response.json()["comments"]}
    bad = comments["Local comment with foreign author"]
    assert bad["author"] is None
    assert bad["author_name"] == ""
    assert f["foreign_author"].username not in str(response.content)
    assert str(f["foreign_author"].pk) not in str(response.content)
    good = comments["Local comment with local author"]
    assert str(good["author"]) == str(f["reporter"].pk)
    assert good["author_name"] == f["reporter"].username



def test_work_order_mutations_cannot_serialize_cross_tenant_comments(school_context):
    """Transition and update bypass the list prefetch; both must fail closed."""
    f = school_context
    client = request_client(f["facilities"], f["school"])
    path = f"/api/facilities/work-orders/{f['own_order'].pk}/"

    for response in (
        client.patch(path, {"description": "Authorized local update"}, format="json"),
        client.post(path + "transition/", {"status": "IN_PROGRESS"}, format="json"),
    ):
        assert response.status_code == 200, (response.status_code, response.content)
        contents = response.json()
        comments = {item["body"]: item for item in contents["comments"]}
        assert "FOREIGN-SCHOOL-PRIVATE-COMMENT" not in comments
        assert "Local comment with local author" in comments
        assert "Local comment with foreign author" in comments
        assert comments["Local comment with foreign author"]["author"] is None
        assert comments["Local comment with foreign author"]["author_name"] == ""
        assert f["foreign_author"].username not in str(response.content)
