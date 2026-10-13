from datetime import date
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from board_oversight import api_governance
from core.models import School, UserRole, CrownPermission, RolePermission


class FakeQuerySet:
    def __init__(self, *, items=None, count_value=None, first_value=None, calls=None):
        self.items = list(items or [])
        self.count_value = len(self.items) if count_value is None else count_value
        self.first_value = first_value
        self.calls = calls if calls is not None else []

    def filter(self, **kwargs):
        self.calls.append(("filter", kwargs))
        return self

    def order_by(self, *fields):
        self.calls.append(("order_by", fields))
        return self

    def first(self):
        self.calls.append(("first", None))
        return self.first_value

    def count(self):
        self.calls.append(("count", None))
        return self.count_value

    def values(self, *fields):
        self.calls.append(("values", fields))
        return self

    def __iter__(self):
        return iter(self.items)


class InitiativeQuerySet(FakeQuerySet):
    def __init__(self, *, items, total, completed, calls=None):
        super().__init__(items=items, count_value=total, calls=calls)
        self.total = total
        self.completed = completed
        self.completed_filter = False

    def filter(self, **kwargs):
        self.calls.append(("filter", kwargs))
        if kwargs == {"status": "complete"}:
            child = InitiativeQuerySet(
                items=self.items,
                total=self.completed,
                completed=self.completed,
                calls=self.calls,
            )
            child.completed_filter = True
            return child
        return self


class FakeManager:
    def __init__(self, queryset):
        self.queryset = queryset

    def filter(self, **kwargs):
        self.queryset.calls.append(("filter", kwargs))
        return self.queryset

    def order_by(self, *fields):
        self.queryset.calls.append(("order_by", fields))
        return self.queryset

    def values(self, *fields):
        self.queryset.calls.append(("values", fields))
        return self.queryset


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def user(db):
    User = get_user_model()
    username_field = User.USERNAME_FIELD
    kwargs = {username_field: "board-test-user"}
    if username_field != "email" and hasattr(User, "email"):
        kwargs["email"] = "board-test@example.com"
    return User.objects.create_user(password="test-password", **kwargs)


def grant_board_access(user, school):
    UserRole.objects.get_or_create(user=user, school=school, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(code="board.view")
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)


def authenticated_get(factory, user, path, school_id=None):
    headers = {}
    if school_id is not None:
        headers["HTTP_X_SCHOOL_ID"] = str(school_id)
    request = factory.get(path, **headers)
    force_authenticate(request, user=user)
    return request


def test_named_board_routes_resolve_to_expected_paths():
    assert reverse("board-packet-download").endswith("/v1/board/packet/download/")
    assert reverse("board-compass").endswith("/v1/board/compass/")
    assert reverse("board-initiatives").endswith("/v1/board/initiatives/")
    assert reverse("board-trends").endswith("/v1/board/trends/")
    assert reverse("board-roadmap").endswith("/v1/board/roadmap/")
    assert reverse("board-releases").endswith("/v1/board/releases/")


@pytest.mark.parametrize(
    "view,path_name",
    [
        (api_governance.download_board_packet, "board-packet-download"),
        (api_governance.compass_executive, "board-compass"),
        (api_governance.initiative_summary, "board-initiatives"),
        (api_governance.board_trends, "board-trends"),
    ],
)
def test_protected_board_endpoints_reject_anonymous_requests(factory, view, path_name):
    response = view(factory.get(reverse(path_name)))

    assert response.status_code in {401, 403}


@pytest.mark.parametrize(
    "view,path_name",
    [
        (api_governance.download_board_packet, "board-packet-download"),
        (api_governance.compass_executive, "board-compass"),
        (api_governance.initiative_summary, "board-initiatives"),
        (api_governance.board_trends, "board-trends"),
    ],
)
def test_protected_board_endpoints_require_valid_school_header(factory, user, view, path_name):
    missing = authenticated_get(factory, user, reverse(path_name))
    invalid = authenticated_get(factory, user, reverse(path_name), "not-a-uuid")

    missing_response = view(missing)
    invalid_response = view(invalid)

    assert missing_response.status_code == 400
    assert missing_response.data == {"detail": "Missing required header: X-School-Id"}
    assert invalid_response.status_code == 400
    assert invalid_response.data == {"detail": "Invalid X-School-Id (must be UUID)"}


def test_download_board_packet_returns_503_when_generation_unavailable(monkeypatch, factory, user):
    school = School.objects.create(name="Packet missing generator")
    school_id = school.id
    grant_board_access(user, school)
    monkeypatch.setattr(api_governance, "generate_board_packet", lambda school_id: None)
    request = authenticated_get(factory, user, reverse("board-packet-download"), school_id)

    response = api_governance.download_board_packet(request)

    assert response.status_code == 503
    assert response.data["detail"].startswith("PDF generation unavailable")


def test_download_board_packet_streams_pdf_with_attachment_headers(monkeypatch, factory, user):
    school = School.objects.create(name="Packet generator")
    school_id = school.id
    grant_board_access(user, school)
    seen = {}

    def generate_board_packet(*, school_id):
        seen["school_id"] = school_id
        return BytesIO(b"%PDF-test")

    monkeypatch.setattr(api_governance, "generate_board_packet", generate_board_packet)
    request = authenticated_get(factory, user, reverse("board-packet-download"), school_id)

    response = api_governance.download_board_packet(request)

    assert response.status_code == 200
    assert response.content == b"%PDF-test"
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "attachment; filename=crown_board_packet.pdf"
    assert seen["school_id"] == school_id


def test_compass_summary_abstains_from_unvalidated_scores(monkeypatch):
    school_id = uuid4()
    empty_calls = []
    monkeypatch.setattr(api_governance.BoardKPISnapshot, "objects",
                        FakeManager(FakeQuerySet(first_value=None, calls=empty_calls)))
    empty = api_governance._compass_summary(school_id=school_id)
    assert empty["overall_score"] is None
    assert empty["source"] == "empty"
    assert empty["source_month"] is None
    assert ("filter", {"school_id": school_id}) in empty_calls

    latest = SimpleNamespace(
        enrollment=140, revenue=Decimal("125000.00"),
        discipline_incidents=60, financial_aid_awards=-5,
        month=date(2026, 7, 1),
    )
    monkeypatch.setattr(api_governance.BoardKPISnapshot, "objects",
                        FakeManager(FakeQuerySet(first_value=latest)))
    populated = api_governance._compass_summary(school_id=school_id)
    assert populated["source"] == "unscored_snapshot"
    assert populated["source_month"] == "2026-07-01"
    assert populated["calculation_status"] == "awaiting_validated_metric_definitions"
    assert all(populated[k] is None for k in (
        "enrollment_health", "financial_health", "discipline_health",
        "spiritual_life_health", "overall_score",
    ))


def test_compass_endpoint_returns_tenant_scoped_summary(monkeypatch, factory, user):
    school = School.objects.create(name="Authorized board testing")
    school_id = school.id
    grant_board_access(user, school)
    expected = {"school_id": str(school_id), "overall_score": 88}
    monkeypatch.setattr(api_governance, "_compass_summary", lambda school_id: expected)
    request = authenticated_get(factory, user, reverse("board-compass"), school_id)

    response = api_governance.compass_executive(request)

    assert response.status_code == 200
    assert response.data == expected


def test_initiative_summary_scopes_counts_and_serializes_items(monkeypatch, factory, user):
    school = School.objects.create(name="Authorized board testing")
    school_id = school.id
    grant_board_access(user, school)
    calls = []
    items = [
        {
            "id": 1,
            "title": "Accreditation",
            "status": "complete",
            "owner_role": "Head of School",
            "target_date": date(2026, 9, 1),
            "progress_percent": 100,
            "created_at": "timestamp",
        }
    ]
    qs = InitiativeQuerySet(items=items, total=4, completed=1, calls=calls)
    monkeypatch.setattr(api_governance.StrategicInitiative, "objects", FakeManager(qs))
    request = authenticated_get(factory, user, reverse("board-initiatives"), school_id)

    response = api_governance.initiative_summary(request)

    assert response.status_code == 200
    assert response.data == {
        "school_id": str(school_id),
        "total_initiatives": 4,
        "completed": 1,
        "completion_rate": 25.0,
        "initiatives": items,
    }
    assert ("filter", {"school_id": school_id}) in calls
    assert ("filter", {"status": "complete"}) in calls


def test_initiative_summary_uses_zero_completion_rate_for_empty_tenant(monkeypatch, factory, user):
    school = School.objects.create(name="Authorized board testing")
    school_id = school.id
    grant_board_access(user, school)
    qs = InitiativeQuerySet(items=[], total=0, completed=0)
    monkeypatch.setattr(api_governance.StrategicInitiative, "objects", FakeManager(qs))
    request = authenticated_get(factory, user, reverse("board-initiatives"), school_id)

    response = api_governance.initiative_summary(request)

    assert response.status_code == 200
    assert response.data["completion_rate"] == 0


def test_board_trends_scopes_fields_and_orders_ascending(monkeypatch, factory, user):
    school = School.objects.create(name="Authorized board testing")
    school_id = school.id
    grant_board_access(user, school)
    calls = []
    rows = [
        {
            "month": date(2026, 6, 1),
            "revenue": Decimal("1000.00"),
            "enrollment": 100,
            "discipline_incidents": 2,
            "financial_aid_awards": 4,
        }
    ]
    qs = FakeQuerySet(items=rows, calls=calls)
    monkeypatch.setattr(api_governance.BoardKPISnapshot, "objects", FakeManager(qs))
    request = authenticated_get(factory, user, reverse("board-trends"), school_id)

    response = api_governance.board_trends(request)

    assert response.status_code == 200
    assert response.data == {"school_id": str(school_id), "trends": rows}
    assert ("filter", {"school_id": school_id}) in calls
    assert (
        "values",
        ("month", "revenue", "enrollment", "discipline_incidents", "financial_aid_awards"),
    ) in calls
    assert ("order_by", ("month",)) in calls


@pytest.mark.parametrize("view,path_name", [
    (api_governance.download_board_packet, "board-packet-download"),
    (api_governance.compass_executive, "board-compass"),
    (api_governance.initiative_summary, "board-initiatives"),
    (api_governance.board_trends, "board-trends"),
])
def test_board_endpoints_deny_ungranted_or_other_school_access(factory, user, view, path_name):
    school_a = School.objects.create(name="Board Authority A")
    school_b = School.objects.create(name="Board Authority B")
    grant_board_access(user, school_a)
    ungranted = view(authenticated_get(factory, user, reverse(path_name), school_b.id))
    assert ungranted.status_code in (403, 404)
    unauthorized_user = get_user_model().objects.create_user(
        username=f"no-board-{uuid4().hex[:8]}", password="Passw0rd!"
    )
    no_grant = view(authenticated_get(factory, unauthorized_user, reverse(path_name), school_a.id))
    assert no_grant.status_code in (403, 404)


def test_public_roadmap_filters_visible_statuses_without_authentication(monkeypatch, factory):
    calls = []
    rows = [
        {
            "title": "Board analytics",
            "description": "Expanded trend analysis",
            "status": "planned",
            "target_release": date(2026, 10, 1),
        }
    ]
    qs = FakeQuerySet(items=rows, calls=calls)
    monkeypatch.setattr(api_governance.RoadmapItem, "objects", FakeManager(qs))

    response = api_governance.public_roadmap(factory.get(reverse("board-roadmap")))

    assert response.status_code == 200
    assert response.data == {"roadmap": rows}
    assert (
        "filter",
        {"status__in": ["planned", "in_progress", "released"]},
    ) in calls
    assert ("values", ("title", "description", "status", "target_release")) in calls


def test_release_notes_are_public_and_serialize_versioned_fields(monkeypatch, factory):
    calls = []
    rows = [
        {
            "version": "crown-0.4.0-rc1",
            "release_date": date(2026, 8, 1),
            "notes": "Release candidate",
        }
    ]
    qs = FakeQuerySet(items=rows, calls=calls)
    monkeypatch.setattr(api_governance.ReleaseLog, "objects", FakeManager(qs))

    response = api_governance.release_notes(factory.get(reverse("board-releases")))

    assert response.status_code == 200
    assert response.data == {"releases": rows}
    assert ("values", ("version", "release_date", "notes")) in calls
