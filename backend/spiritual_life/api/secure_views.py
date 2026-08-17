"""Persistent-RBAC adapters for the legacy Spiritual Life API classes."""

from core.permissions import CrownModulePermission
from spiritual_life.api import views as legacy

_NAMES = [
    "SpiritualProfileView",
    "SpiritualProfileDetailView",
    "SpiritualAssessmentListCreate",
    "ChapelEventListCreate",
    "ChapelEventDetail",
    "ChapelAttendanceListCreate",
    "SmallGroupListCreate",
    "SmallGroupMemberListCreate",
    "SmallGroupSessionListCreate",
    "SmallGroupSessionAttendanceView",
    "PrayerRequestListCreate",
    "PrayerRequestDetail",
    "PastoralNoteListCreate",
    "PastoralNoteDetail",
]


def _secure(base):
    return type(
        base.__name__,
        (base,),
        {
            "__module__": __name__,
            "permission_classes": [CrownModulePermission("spiritual_life.view")],
        },
    )


for _name in _NAMES:
    globals()[_name] = _secure(getattr(legacy, _name))

__all__ = _NAMES
