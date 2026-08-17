from django.urls import include, path

from spiritual_life.api.permissions import SpiritualLifePermission
from spiritual_life.api.secure_sensitive_views import (
    SecurePastoralNoteDetail,
    SecurePastoralNoteListCreate,
    SecurePrayerRequestDetail,
    SecurePrayerRequestListCreate,
)
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
)


SPIRITUAL_LIFE_PERMISSIONS = [SpiritualLifePermission]

urlpatterns = [
    path("profiles/", SpiritualProfileView.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="spiritual_profiles"),
    path("profiles/<uuid:profile_id>/", SpiritualProfileDetailView.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="spiritual_profile_detail"),
    path("assessments/", SpiritualAssessmentListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="spiritual_assessments"),
    path("chapel-events/", ChapelEventListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="chapel_events"),
    path("chapel-events/<uuid:event_id>/", ChapelEventDetail.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="chapel_event_detail"),
    path("chapel-events/<uuid:event_id>/attendance/", ChapelAttendanceListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="chapel_attendance"),
    path("small-groups/", SmallGroupListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="small_groups"),
    path("small-groups/<uuid:group_id>/members/", SmallGroupMemberListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="small_group_members"),
    path("small-groups/<uuid:group_id>/sessions/", SmallGroupSessionListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="small_group_sessions"),
    path("small-group-sessions/<uuid:session_id>/attendance/", SmallGroupSessionAttendanceView.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="small_group_attendance"),
    path("prayer-requests/", SecurePrayerRequestListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="prayer_requests"),
    path("prayer-requests/<uuid:pr_id>/", SecurePrayerRequestDetail.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="prayer_request_detail"),
    path("pastoral-notes/", SecurePastoralNoteListCreate.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="pastoral_notes"),
    path("pastoral-notes/<uuid:note_id>/", SecurePastoralNoteDetail.as_view(permission_classes=SPIRITUAL_LIFE_PERMISSIONS), name="pastoral_note_detail"),
    path("formation/", include("spiritual_life.api.formation_urls")),
]
