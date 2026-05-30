from django.urls import include, path

from spiritual_life.api.views import (
    SpiritualProfileView,
    SpiritualProfileDetailView,
    SpiritualAssessmentListCreate,
    ChapelEventListCreate,
    ChapelEventDetail,
    ChapelAttendanceListCreate,
    SmallGroupListCreate,
    SmallGroupMemberListCreate,
    SmallGroupSessionListCreate,
    SmallGroupSessionAttendanceView,
    PrayerRequestListCreate,
    PrayerRequestDetail,
    PastoralNoteListCreate,
    PastoralNoteDetail,
)

urlpatterns = [
    # Student Spiritual Profiles
    path("profiles/", SpiritualProfileView.as_view(), name="spiritual_profiles"),
    path(
        "profiles/<uuid:profile_id>/",
        SpiritualProfileDetailView.as_view(),
        name="spiritual_profile_detail",
    ),
    # Spiritual Assessments
    path(
        "assessments/",
        SpiritualAssessmentListCreate.as_view(),
        name="spiritual_assessments",
    ),
    # Chapel Events
    path("chapel-events/", ChapelEventListCreate.as_view(), name="chapel_events"),
    path(
        "chapel-events/<uuid:event_id>/",
        ChapelEventDetail.as_view(),
        name="chapel_event_detail",
    ),
    path(
        "chapel-events/<uuid:event_id>/attendance/",
        ChapelAttendanceListCreate.as_view(),
        name="chapel_attendance",
    ),
    # Small Groups
    path("small-groups/", SmallGroupListCreate.as_view(), name="small_groups"),
    path(
        "small-groups/<uuid:group_id>/members/",
        SmallGroupMemberListCreate.as_view(),
        name="small_group_members",
    ),
    path(
        "small-groups/<uuid:group_id>/sessions/",
        SmallGroupSessionListCreate.as_view(),
        name="small_group_sessions",
    ),
    path(
        "small-group-sessions/<uuid:session_id>/attendance/",
        SmallGroupSessionAttendanceView.as_view(),
        name="small_group_attendance",
    ),
    # Prayer Requests
    path(
        "prayer-requests/",
        PrayerRequestListCreate.as_view(),
        name="prayer_requests",
    ),
    path(
        "prayer-requests/<uuid:pr_id>/",
        PrayerRequestDetail.as_view(),
        name="prayer_request_detail",
    ),
    # Pastoral Notes - staff only
    path("pastoral-notes/", PastoralNoteListCreate.as_view(), name="pastoral_notes"),
    path(
        "pastoral-notes/<uuid:note_id>/",
        PastoralNoteDetail.as_view(),
        name="pastoral_note_detail",
    ),
    # Spiritual Life & Biblical Formation expansion
    path("formation/", include("spiritual_life.api.formation_urls")),
]
