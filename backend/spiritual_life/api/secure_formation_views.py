"""Persistent-RBAC adapters for Spiritual Life formation views."""

from core.permissions import CrownModulePermission
from spiritual_life.api import formation_views as legacy

_NAMES = [
    "BiblicalIntegrationRecordListCreate",
    "BiblicalWorldviewPriorityDetail",
    "BiblicalWorldviewPriorityListCreate",
    "CallingPathwayEventListCreate",
    "ChristianEducationSundayCampaignListCreate",
    "ChurchEngagementEventDetail",
    "ChurchEngagementEventListCreate",
    "ChurchPartnerDetail",
    "ChurchPartnerListCreate",
    "CommunityOrganizationPartnerListCreate",
    "DevotionalContentDetail",
    "DevotionalContentListCreate",
    "FamilyFormationEventListCreate",
    "FormationArtifactDetail",
    "FormationArtifactListCreate",
    "FormationCampaignDetail",
    "FormationCampaignListCreate",
    "FormationMissionControlSummary",
    "PastorContactDetail",
    "PastorContactListCreate",
    "PortraitDomainDetail",
    "PortraitDomainListCreate",
    "SpeakerVettingRecordListCreate",
    "SpiritualCareCaseDetail",
    "SpiritualCareCaseListCreate",
    "SpiritualDomainRatingListCreate",
    "StaffFormationEventListCreate",
    "StudentLeadershipEventListCreate",
    "StudentSpiritualLeadershipRoleListCreate",
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
