"""Camp theme-week and reusable club/elective regressions."""
from datetime import date, time
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crown_api.audit_models import AuditEvent
from households.models import Guardian, Household, Student
from summer_camp import api
from summer_camp.models import (
    SummerCampClub, SummerCampClubOffering, SummerCampClubSelection,
    SummerCampEnrollment, SummerCampProgram, SummerCampSession,
)
from summer_camp.services import (
    cancel_club_selection, create_club, create_club_offering, select_club,
    update_club_offering,
)

pytestmark = pytest.mark.django_db


def case(label="A"):
    school = School.objects.create(name=f"Camp Catalog {label}")
    household = Household.objects.create(school_id=school.id, name=f"Family {label}")
    student = Student.objects.create(
        school_id=school.id, household=household, first_name="Camper",
        last_name=label, grade_level="4",
    )
    program = SummerCampProgram.objects.create(school=school, name=f"Program {label}")
    session = SummerCampSession.objects.create(
        school=school, program=program, name=f"Week {label}",
        theme_title="Courage", theme_story="A week about resilient service.",
        scripture_reference="Joshua 1:9", virtue_focus="Courage",
        special_event="Friday service project", start_date=date(2027, 6, 14),
        end_date=date(2027, 6, 18), start_time=time(8), end_time=time(16),
        capacity=20, waitlist_capacity=5, status="PUBLISHED",
    )
    enrollment = SummerCampEnrollment.objects.create(
        school=school, session=session, student=student, household=household,
        status="REGISTERED",
    )
    return school, household, student, session, enrollment


def extra_enrollment(school, session, label):
    household = Household.objects.create(school_id=school.id, name=f"Family {label}")
    student = Student.objects.create(
        school_id=school.id, household=household, first_name="Camper",
        last_name=label, grade_level="5",
    )
    return SummerCampEnrollment.objects.create(
        school=school, session=session, student=student, household=household,
        status="REGISTERED",
    )


def club(school, code="stem"):
    return create_club(school.id, {
        "code": code, "name": code.replace("-", " ").title(),
        "category": "STEM", "description": "Synthetic club",
    })


def offering(
    school, session, catalog, *, start=time(10), end=time(11),
    capacity=1, waitlist=1, weekdays=None, instructor_id=None,
):
    payload = {
        "session_id": session.id, "club_id": catalog.id,
        "weekdays": weekdays or [0, 2, 4], "start_time": start, "end_time": end,
        "location": "Room 101", "capacity": capacity,
        "waitlist_capacity": waitlist, "optional_charge_cents": 2500,
        "status": "PUBLISHED",
    }
    if instructor_id is not None:
        payload["instructor_id"] = instructor_id
    return create_club_offering(school.id, payload)


def grant(user, school, *codes):
    role = f"camp_catalog_{uuid4().hex[:12]}"
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=permission)


def parent_for(school, household, label):
    user = UserAccount.objects.create_user(
        username=f"camp-parent-{label}-{uuid4().hex[:8]}",
        password="unused", school=school,
    )
    Guardian.objects.create(
        school_id=school.id, household=household, account=user,
        first_name="Pat", last_name="Guardian", is_primary=True,
    )
    return user


def request(factory, method, path, user, school, data=None):
    req = getattr(factory, method)(path, data or {}, format="json")
    req.school = school
    req.tenant_school_id = school.id
    force_authenticate(req, user=user)
    return req


def test_theme_fields_are_optional_and_preserve_faith_context():
    school, _household, _student, session, _enrollment = case("Theme")
    session.refresh_from_db()
    assert (
        session.theme_title, session.scripture_reference, session.virtue_focus,
        session.special_event,
    ) == ("Courage", "Joshua 1:9", "Courage", "Friday service project")
    general = SummerCampSession.objects.create(
        school=school, program=session.program, name="General Purpose Week",
        start_date=date(2027, 6, 21), end_date=date(2027, 6, 25),
        start_time=time(8), end_time=time(16), capacity=10, status="DRAFT",
    )
    assert (general.theme_title, general.scripture_reference, general.virtue_focus) == ("", "", "")


def test_offering_rejects_cross_tenant_and_invalid_instructors():
    school, _h, _s, session, _e = case("Home")
    foreign, _fh, _fs, _foreign_session, _fe = case("Foreign")
    catalog = club(school)
    with pytest.raises(ValueError, match="unavailable session or catalog item"):
        create_club_offering(foreign.id, {
            "session_id": session.id, "club_id": catalog.id, "weekdays": [1],
            "start_time": time(9), "end_time": time(10), "capacity": 10,
            "status": "PUBLISHED",
        })

    foreign_user = UserAccount.objects.create_user(
        username=f"foreign-instructor-{uuid4().hex[:8]}", password="unused",
        school=foreign,
    )
    inactive = UserAccount.objects.create_user(
        username=f"inactive-instructor-{uuid4().hex[:8]}", password="unused",
        school=school, is_active=False,
    )
    for instructor_id in (foreign_user.id, inactive.id, uuid4()):
        with pytest.raises(ValueError, match="active member of this school"):
            offering(school, session, catalog, instructor_id=instructor_id)
    assert not SummerCampClubOffering.objects.filter(school=school, club=catalog).exists()

    valid = UserAccount.objects.create_user(
        username=f"valid-instructor-{uuid4().hex[:8]}", password="unused",
        school=school,
    )
    scheduled = offering(school, session, catalog, instructor_id=valid.id)
    with pytest.raises(ValueError, match="active member of this school"):
        update_club_offering(
            school.id, scheduled.id, {"instructor_id": foreign_user.id}
        )
    scheduled.refresh_from_db()
    assert scheduled.instructor_id == valid.id


def test_capacity_waitlist_saturation_and_promotion_are_deterministic():
    school, _h, _s, session, first = case("Seats")
    second = extra_enrollment(school, session, "Second")
    third = extra_enrollment(school, session, "Third")
    scheduled = offering(school, session, club(school, "robotics"))
    selected = select_club(school.id, first.id, scheduled.id)
    queued = select_club(school.id, second.id, scheduled.id)
    assert (selected.status, queued.status, queued.waitlist_position) == (
        "ENROLLED", "WAITLISTED", 1,
    )
    with pytest.raises(ValueError, match="no remaining capacity"):
        select_club(school.id, third.id, scheduled.id)
    cancelled, promoted = cancel_club_selection(school.id, selected.id)
    queued.refresh_from_db()
    assert cancelled.status == "CANCELLED"
    assert promoted.id == queued.id
    assert (queued.status, queued.waitlist_position) == ("ENROLLED", None)


def test_schedule_conflict_denied_but_adjacent_activity_allowed():
    school, _h, _s, session, enrollment = case("Schedule")
    first = offering(
        school, session, club(school, "arts"), start=time(10), end=time(11),
        capacity=10, waitlist=0, weekdays=[1, 3],
    )
    overlap = offering(
        school, session, club(school, "leadership"), start=time(10, 30),
        end=time(11, 30), capacity=10, waitlist=0, weekdays=[3],
    )
    later = offering(
        school, session, club(school, "service"), start=time(11), end=time(12),
        capacity=10, waitlist=0, weekdays=[1, 3],
    )
    assert select_club(school.id, enrollment.id, first.id).status == "ENROLLED"
    with pytest.raises(ValueError, match="conflicts"):
        select_club(school.id, enrollment.id, overlap.id)
    assert select_club(school.id, enrollment.id, later.id).status == "ENROLLED"


def test_published_offering_validation_and_selected_schedule_immutability():
    school, _h, _s, session, enrollment = case("Publish")
    catalog = club(school, "reading")
    with pytest.raises(ValidationError, match="weekday"):
        create_club_offering(school.id, {
            "session_id": session.id, "club_id": catalog.id, "weekdays": [],
            "start_time": time(9), "end_time": time(10), "capacity": 5,
            "status": "PUBLISHED",
        })
    scheduled = offering(
        school, session, catalog, start=time(9), end=time(10), capacity=2,
    )
    select_club(school.id, enrollment.id, scheduled.id)
    with pytest.raises(ValueError, match="cannot change after camper selection"):
        update_club_offering(school.id, scheduled.id, {"start_time": time(9, 30)})
    with pytest.raises(ValueError, match="lower than enrolled selections"):
        update_club_offering(school.id, scheduled.id, {"capacity": 0})
    assert update_club_offering(
        school.id, scheduled.id, {"location": "Innovation Lab"}
    ).location == "Innovation Lab"


def test_selection_model_rejects_inconsistent_waitlist_state():
    school, _h, _s, session, enrollment = case("WaitlistState")
    scheduled = offering(school, session, club(school, "state"), capacity=2)
    with pytest.raises(ValidationError, match="waitlist position"):
        SummerCampClubSelection.objects.create(
            school=school, offering=scheduled, enrollment=enrollment,
            status="WAITLISTED", waitlist_position=None,
        )
    with pytest.raises(ValidationError, match="Only waitlisted"):
        SummerCampClubSelection.objects.create(
            school=school, offering=scheduled, enrollment=enrollment,
            status="ENROLLED", waitlist_position=1,
        )


def test_staff_api_requires_explicit_school_scoped_view_and_edit(monkeypatch):
    school, _h, _s, _session, _enrollment = case("Api")
    user = UserAccount.objects.create_user(
        username=f"camp-api-{uuid4().hex[:8]}", password="unused", school=school,
    )
    factory = APIRequestFactory()
    monkeypatch.setattr(api, "school_id_from_request", lambda req, required=True: school.id)

    assert api.clubs_view(request(
        factory, "get", "/api/v1/summer-camp/clubs/", user, school
    )).status_code == 403
    grant(user, school, "summer_camp.view")
    assert api.clubs_view(request(
        factory, "get", "/api/v1/summer-camp/clubs/", user, school
    )).status_code == 200
    payload = {"code": "stem", "name": "STEM", "category": "STEM"}
    assert api.clubs_view(request(
        factory, "post", "/api/v1/summer-camp/clubs/", user, school, payload
    )).status_code == 403
    grant(user, school, "summer_camp.edit")
    response = api.clubs_view(request(
        factory, "post", "/api/v1/summer-camp/clubs/", user, school, payload
    ))
    assert response.status_code == 201
    assert SummerCampClub.objects.filter(school=school, code="stem").count() == 1


def test_guardian_discovery_selection_and_cancel_are_household_scoped(monkeypatch):
    school, household, _student, session, own = case("Parent")
    other = extra_enrollment(school, session, "OtherFamily")
    catalog = club(school, "service")
    scheduled = offering(
        school, session, catalog, capacity=3, waitlist=1, weekdays=[1, 3],
    )
    parent = parent_for(school, household, "own")
    factory = APIRequestFactory()
    monkeypatch.setattr(api, "school_id_from_request", lambda req, required=True: school.id)

    own_path = f"/api/v1/summer-camp/club-offerings/?enrollment_id={own.id}"
    response = api.club_offerings_view(request(factory, "get", own_path, parent, school))
    assert response.status_code == 200
    assert [row["id"] for row in response.data] == [scheduled.id]
    other_path = f"/api/v1/summer-camp/club-offerings/?enrollment_id={other.id}"
    assert api.club_offerings_view(request(
        factory, "get", other_path, parent, school
    )).status_code == 403

    own_payload = {"enrollment_id": own.id, "offering_id": scheduled.id}
    selected = api.club_selections_view(request(
        factory, "post", "/api/v1/summer-camp/club-selections/",
        parent, school, own_payload,
    ))
    assert selected.status_code == 201
    assert api.club_selections_view(request(
        factory, "post", "/api/v1/summer-camp/club-selections/",
        parent, school, {"enrollment_id": other.id, "offering_id": scheduled.id},
    )).status_code == 403

    other_selection = select_club(school.id, other.id, scheduled.id)
    foreign_cancel = request(
        factory, "post",
        f"/api/v1/summer-camp/club-selections/{other_selection.id}/cancel/",
        parent, school,
    )
    assert api.club_selection_cancel_view(
        foreign_cancel, other_selection.id
    ).status_code == 403
    own_cancel = request(
        factory, "post",
        f"/api/v1/summer-camp/club-selections/{selected.data['id']}/cancel/",
        parent, school,
    )
    assert api.club_selection_cancel_view(
        own_cancel, selected.data["id"]
    ).data["status"] == "CANCELLED"
    actions = list(
        AuditEvent.objects.filter(school_id=school.id).order_by("ts")
        .values_list("action", flat=True)
    )
    assert "summer_camp.club_selection.created" in actions
    assert "summer_camp.club_selection.cancelled" in actions


def test_guardian_lists_only_owned_selection_and_inactive_club_is_hidden(monkeypatch):
    school, household, _student, session, enrollment = case("ParentList")
    catalog = club(school, "reading-club")
    scheduled = offering(school, session, catalog, capacity=5, waitlist=0)
    selection = select_club(school.id, enrollment.id, scheduled.id)
    parent = parent_for(school, household, "list")
    factory = APIRequestFactory()
    monkeypatch.setattr(api, "school_id_from_request", lambda req, required=True: school.id)

    assert api.club_selections_view(request(
        factory, "get", "/api/v1/summer-camp/club-selections/", parent, school
    )).status_code == 403
    scoped = api.club_selections_view(request(
        factory, "get",
        f"/api/v1/summer-camp/club-selections/?enrollment_id={enrollment.id}",
        parent, school,
    ))
    assert scoped.status_code == 200
    assert [row["id"] for row in scoped.data] == [selection.id]

    catalog.is_active = False
    catalog.save(update_fields=["is_active"])
    hidden = api.club_offerings_view(request(
        factory, "get",
        f"/api/v1/summer-camp/club-offerings/?enrollment_id={enrollment.id}",
        parent, school,
    ))
    assert hidden.status_code == 200
    assert hidden.data == []
