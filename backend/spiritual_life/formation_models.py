from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class FormationTimeStampedModel(models.Model):
    """Shared timestamped base for Spiritual Life & Biblical Formation records."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = "spiritual_life"


class PortraitDomain(FormationTimeStampedModel):
    """A school-defined Portrait of the Graduate formation outcome."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="portrait_domains")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    scripture_anchor = models.CharField(max_length=160, blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["school", "is_active"])]

    def __str__(self) -> str:
        return self.name


class BiblicalWorldviewPriority(FormationTimeStampedModel):
    """Annual or semester Biblical worldview priority used to align formation work."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="worldview_priorities")
    title = models.CharField(max_length=160)
    scripture_anchor = models.CharField(max_length=160, blank=True, default="")
    description = models.TextField(blank=True, default="")
    grade_band = models.CharField(max_length=40, blank=True, default="")
    school_year = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["school_year", "title"]
        indexes = [models.Index(fields=["school", "school_year", "is_active"])]

    def __str__(self) -> str:
        return self.title


class FormationCampaign(FormationTimeStampedModel):
    """A schoolwide formation campaign such as Spiritual Emphasis Week or Missions Week."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("planned", "Planned"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="formation_campaigns")
    name = models.CharField(max_length=180)
    theme = models.CharField(max_length=180, blank=True, default="")
    scripture_anchor = models.CharField(max_length=160, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="draft")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="formation_campaigns_owned",
    )
    summary = models.TextField(blank=True, default="")
    portrait_domains = models.ManyToManyField(PortraitDomain, blank=True, related_name="campaigns")
    worldview_priorities = models.ManyToManyField(BiblicalWorldviewPriority, blank=True, related_name="campaigns")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-start_date", "name"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return self.name


class FormationArtifact(FormationTimeStampedModel):
    """Evidence artifact linking real formation work to Portrait and worldview priorities."""

    ARTIFACT_TYPES = [
        ("chapel", "Chapel"),
        ("devotion", "Devotion"),
        ("article", "Article"),
        ("small_group", "Small Group"),
        ("service", "Service Project"),
        ("staff_formation", "Staff Formation"),
        ("family_resource", "Family Resource"),
        ("assessment", "Assessment"),
        ("church_engagement", "Church Engagement"),
        ("student_leadership", "Student Leadership"),
        ("calling_pathway", "Calling Pathway"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="formation_artifacts")
    artifact_type = models.CharField(max_length=40, choices=ARTIFACT_TYPES)
    title = models.CharField(max_length=180)
    artifact_date = models.DateField(null=True, blank=True)
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    evidence_url = models.URLField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="formation_artifacts_created",
    )
    campaigns = models.ManyToManyField(FormationCampaign, blank=True, related_name="artifacts")
    portrait_domains = models.ManyToManyField(PortraitDomain, blank=True, related_name="artifacts")
    worldview_priorities = models.ManyToManyField(BiblicalWorldviewPriority, blank=True, related_name="artifacts")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-artifact_date", "-created_at"]
        indexes = [models.Index(fields=["school", "artifact_type"])]

    def __str__(self) -> str:
        return f"{self.artifact_type}: {self.title}"


class DevotionalContent(FormationTimeStampedModel):
    """Reviewed devotional content for students, families, staff, and chapel follow-up."""

    AUDIENCE_CHOICES = [
        ("lower_elementary", "Lower Elementary"),
        ("upper_elementary", "Upper Elementary"),
        ("middle_school", "Middle School"),
        ("high_school", "High School"),
        ("staff", "Staff"),
        ("family", "Family"),
        ("student_leaders", "Student Leaders"),
        ("whole_school", "Whole School"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="devotional_contents")
    title = models.CharField(max_length=180)
    audience = models.CharField(max_length=40, choices=AUDIENCE_CHOICES)
    grade_band = models.CharField(max_length=40, blank=True, default="")
    week_number = models.PositiveIntegerField(default=0)
    publish_date = models.DateField(null=True, blank=True)
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    theme = models.CharField(max_length=160, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    body = models.TextField(blank=True, default="")
    reflection_question = models.TextField(blank=True, default="")
    prayer_focus = models.TextField(blank=True, default="")
    family_prompt = models.TextField(blank=True, default="")
    staff_connection = models.TextField(blank=True, default="")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="draft")
    is_published = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="devotionals_reviewed",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    portrait_domains = models.ManyToManyField(PortraitDomain, blank=True, related_name="devotionals")
    worldview_priorities = models.ManyToManyField(BiblicalWorldviewPriority, blank=True, related_name="devotionals")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-publish_date", "audience", "title"]
        indexes = [models.Index(fields=["school", "audience", "status"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.audience})"


class BiblicalIntegrationRecord(FormationTimeStampedModel):
    """Classroom or program record showing Biblical worldview integration."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="biblical_integration_records")
    student = models.ForeignKey(
        "core.Student",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="biblical_integration_records",
    )
    grade_label = models.CharField(max_length=40, blank=True, default="")
    subject = models.CharField(max_length=120, blank=True, default="")
    integration_date = models.DateField(null=True, blank=True)
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="biblical_integrations_created",
    )

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-integration_date", "-created_at"]
        indexes = [models.Index(fields=["school", "integration_date"])]

    def __str__(self) -> str:
        return f"BiblicalIntegration({self.subject}, {self.integration_date})"


class SpiritualDomainRating(FormationTimeStampedModel):
    """Operational rating for a Portrait/worldview formation domain."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="spiritual_domain_ratings")
    student = models.ForeignKey(
        "core.Student",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spiritual_domain_ratings",
    )
    domain = models.ForeignKey(
        PortraitDomain,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ratings",
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    rating_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-rating_date", "-created_at"]
        indexes = [models.Index(fields=["school", "rating_date"])]

    def __str__(self) -> str:
        return f"SpiritualDomainRating({self.rating})"


class SpiritualCareCase(FormationTimeStampedModel):
    """Pastoral-care case with clear referral and safeguarding boundaries."""

    CASE_TYPES = [
        ("prayer_followup", "Prayer Follow-Up"),
        ("pastoral_conversation", "Pastoral Conversation"),
        ("discipleship", "Discipleship"),
        ("grief_crisis", "Grief / Crisis Support"),
        ("church_connection", "Church Connection"),
        ("restoration", "Restoration / Reconciliation"),
        ("referral", "Referral Needed"),
        ("staff_care", "Staff Care"),
        ("family_care", "Family Care"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("monitoring", "Monitoring"),
        ("referred", "Referred"),
        ("closed", "Closed"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="spiritual_care_cases")
    student = models.ForeignKey(
        "core.Student",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spiritual_care_cases",
    )
    prayer_request = models.ForeignKey(
        "spiritual_life.PrayerRequest",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="care_cases",
    )
    case_type = models.CharField(max_length=40, choices=CASE_TYPES)
    title = models.CharField(max_length=180)
    summary = models.TextField(blank=True, default="")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spiritual_care_cases_owned",
    )
    next_follow_up_date = models.DateField(null=True, blank=True)
    parent_notified = models.BooleanField(default=False)
    counselor_referral = models.BooleanField(default=False)
    admin_review_required = models.BooleanField(default=False)
    mandated_reporting_concern = models.BooleanField(default=False)
    outside_referral_made = models.BooleanField(default=False)
    sensitive = models.BooleanField(default=True)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-updated_at", "-created_at"]
        indexes = [models.Index(fields=["school", "status", "priority"])]

    def __str__(self) -> str:
        return f"SpiritualCareCase({self.title}, {self.status})"


class ChurchPartner(FormationTimeStampedModel):
    """Church partner relationship for pastor relations and Christian education outreach."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="church_partners")
    name = models.CharField(max_length=180)
    denomination = models.CharField(max_length=120, blank=True, default="")
    website = models.URLField(blank=True, default="")
    address = models.CharField(max_length=240, blank=True, default="")
    is_active_partner = models.BooleanField(default=True)
    relationship_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="church_partnerships_owned",
    )
    partnership_notes = models.TextField(blank=True, default="")
    next_follow_up_date = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["name"]
        indexes = [models.Index(fields=["school", "is_active_partner"])]

    def __str__(self) -> str:
        return self.name


class PastorContact(FormationTimeStampedModel):
    """Pastor, youth pastor, or ministry leader attached to a church partner."""

    CONTACT_TYPES = [
        ("senior_pastor", "Senior Pastor"),
        ("youth_pastor", "Youth Pastor"),
        ("children_ministry", "Children's Ministry"),
        ("missions", "Missions"),
        ("admin", "Administrative Contact"),
        ("other", "Other"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="pastor_contacts")
    church = models.ForeignKey(ChurchPartner, on_delete=models.CASCADE, related_name="contacts")
    contact_type = models.CharField(max_length=40, choices=CONTACT_TYPES, default="other")
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    is_primary = models.BooleanField(default=False)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["church__name", "name"]
        indexes = [models.Index(fields=["school", "contact_type"])]

    def __str__(self) -> str:
        return self.name


class ChurchEngagementEvent(FormationTimeStampedModel):
    """Guest speaking, church visit, pastor luncheon, tour, or community ministry event."""

    EVENT_TYPES = [
        ("guest_speaking", "Guest Speaking"),
        ("christian_education_sunday", "Christian Education Sunday"),
        ("church_visit", "Church Visit"),
        ("pastor_luncheon", "Pastor Luncheon"),
        ("pastor_tour", "Pastor Campus Tour"),
        ("pastor_meeting", "Pastor Meeting"),
        ("youth_ministry_event", "Youth Ministry Event"),
        ("community_org_meeting", "Community Organization Meeting"),
        ("service_partnership", "Service Partnership"),
        ("prayer_event", "Prayer Event"),
        ("ministry_fair", "Ministry Fair"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("follow_up_needed", "Follow-Up Needed"),
        ("closed", "Closed"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="church_engagement_events")
    church_partner = models.ForeignKey(
        ChurchPartner,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="engagement_events",
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    title = models.CharField(max_length=180)
    event_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=180, blank=True, default="")
    audience = models.CharField(max_length=120, blank=True, default="")
    topic = models.CharField(max_length=180, blank=True, default="")
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    speaker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="church_engagements_speaking",
    )
    materials_needed = models.TextField(blank=True, default="")
    school_story_notes = models.TextField(blank=True, default="")
    follow_up_notes = models.TextField(blank=True, default="")
    follow_up_due = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="planned")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-event_date", "title"]
        indexes = [models.Index(fields=["school", "event_type", "status"])]

    def __str__(self) -> str:
        return self.title


class ChristianEducationSundayCampaign(FormationTimeStampedModel):
    """Church-facing campaign to promote and pray for Christian education."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="christian_education_sunday_campaigns")
    name = models.CharField(max_length=180)
    school_year = models.CharField(max_length=20, blank=True, default="")
    campaign_date = models.DateField(null=True, blank=True)
    theme = models.CharField(max_length=180, blank=True, default="")
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    message_summary = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="christian_education_campaigns_owned",
    )
    churches = models.ManyToManyField(ChurchPartner, blank=True, related_name="christian_education_campaigns")
    bulletin_insert_ready = models.BooleanField(default=False)
    slideshow_ready = models.BooleanField(default=False)
    student_testimony_ready = models.BooleanField(default=False)
    family_invitation_sent = models.BooleanField(default=False)
    admissions_follow_up_complete = models.BooleanField(default=False)
    thank_you_sent = models.BooleanField(default=False)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-campaign_date", "name"]
        indexes = [models.Index(fields=["school", "school_year"])]

    def __str__(self) -> str:
        return self.name


class CommunityOrganizationPartner(FormationTimeStampedModel):
    """Community ministry, nonprofit, Christian college, or civic partner."""

    PARTNER_TYPES = [
        ("ministry", "Ministry"),
        ("nonprofit", "Nonprofit"),
        ("church_network", "Church Network"),
        ("business_group", "Business / Civic Group"),
        ("college", "College / University"),
        ("missions", "Missions Organization"),
        ("service_agency", "Service Agency"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="community_organization_partners")
    name = models.CharField(max_length=180)
    partner_type = models.CharField(max_length=40, choices=PARTNER_TYPES)
    contact_name = models.CharField(max_length=120, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    website = models.URLField(blank=True, default="")
    relationship_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="community_partnerships_owned",
    )
    partnership_notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["name"]
        indexes = [models.Index(fields=["school", "partner_type", "is_active"])]

    def __str__(self) -> str:
        return self.name


class StudentSpiritualLeadershipRole(FormationTimeStampedModel):
    """Student spiritual leadership pipeline role."""

    ROLE_TYPES = [
        ("chapel_host", "Chapel Host"),
        ("scripture_reader", "Scripture Reader"),
        ("student_prayer", "Student Prayer"),
        ("worship_team", "Worship Team"),
        ("tech_team", "Chapel Tech Team"),
        ("small_group_leader", "Small Group Leader"),
        ("peer_mentor", "Peer Mentor"),
        ("service_captain", "Service Project Captain"),
        ("testimony_speaker", "Testimony Speaker"),
        ("student_ambassador", "Student Ambassador"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="student_spiritual_leadership_roles")
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE, related_name="spiritual_leadership_roles")
    role_type = models.CharField(max_length=40, choices=ROLE_TYPES)
    title = models.CharField(max_length=160)
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spiritual_leadership_mentees",
    )
    training_completed = models.BooleanField(default=False)
    parent_permission = models.BooleanField(default=False)
    testimony_approved = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["student__last_name", "student__first_name", "role_type"]
        indexes = [models.Index(fields=["school", "role_type", "active"])]

    def __str__(self) -> str:
        return f"{self.student_id}: {self.role_type}"


class StudentLeadershipEvent(FormationTimeStampedModel):
    """Leadership summit, chapel retreat, peer mentor training, or commissioning event."""

    EVENT_TYPES = [
        ("summit", "Student Leadership Summit"),
        ("retreat", "Retreat"),
        ("training", "Training"),
        ("commissioning", "Commissioning"),
        ("prayer_breakfast", "Prayer Leader Breakfast"),
        ("worldview_forum", "Biblical Worldview Forum"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="student_leadership_events")
    title = models.CharField(max_length=180)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES, default="training")
    event_date = models.DateField(null=True, blank=True)
    theme = models.CharField(max_length=180, blank=True, default="")
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="student_leadership_events_facilitated",
    )
    training_objective = models.TextField(blank=True, default="")
    follow_up_assignments = models.TextField(blank=True, default="")
    attendees = models.ManyToManyField("core.Student", blank=True, related_name="spiritual_leadership_events")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-event_date", "title"]
        indexes = [models.Index(fields=["school", "event_type"])]

    def __str__(self) -> str:
        return self.title


class CallingPathwayEvent(FormationTimeStampedModel):
    """Christian college, missions, ministry, vocation, or calling pathway event."""

    EVENT_TYPES = [
        ("christian_college_day", "Christian College Info Day"),
        ("bible_college_preview", "Bible College / Seminary Preview"),
        ("missions_fair", "Missions / Gap-Year Fair"),
        ("ministry_vocation_day", "Ministry Vocation Day"),
        ("alumni_calling_panel", "Alumni Calling Panel"),
        ("senior_calling_week", "Senior Calling Week"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="calling_pathway_events")
    title = models.CharField(max_length=180)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    event_date = models.DateField(null=True, blank=True)
    partner_name = models.CharField(max_length=180, blank=True, default="")
    representative_name = models.CharField(max_length=120, blank=True, default="")
    representative_email = models.EmailField(blank=True, default="")
    grade_levels_invited = models.CharField(max_length=120, blank=True, default="")
    student_interest_count = models.PositiveIntegerField(default=0)
    parent_info_sent = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-event_date", "title"]
        indexes = [models.Index(fields=["school", "event_type"])]

    def __str__(self) -> str:
        return self.title


class FamilyFormationEvent(FormationTimeStampedModel):
    """Parent/family discipleship event or resource release."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="family_formation_events")
    title = models.CharField(max_length=180)
    event_date = models.DateField(null=True, blank=True)
    topic = models.CharField(max_length=180, blank=True, default="")
    speaker = models.CharField(max_length=160, blank=True, default="")
    resource_url = models.URLField(blank=True, default="")
    family_discussion_guide = models.TextField(blank=True, default="")
    attendance_count = models.PositiveIntegerField(default=0)
    follow_up_notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-event_date", "title"]
        indexes = [models.Index(fields=["school", "event_date"])]

    def __str__(self) -> str:
        return self.title


class StaffFormationEvent(FormationTimeStampedModel):
    """Staff devotion, retreat, prayer rhythm, or Biblical worldview PD."""

    EVENT_TYPES = [
        ("devotion", "Staff Devotion"),
        ("prayer", "Staff Prayer"),
        ("worldview_pd", "Biblical Worldview PD"),
        ("retreat", "Staff Retreat"),
        ("onboarding", "New Teacher Formation Onboarding"),
        ("care", "Staff Care"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="staff_formation_events")
    title = models.CharField(max_length=180)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    event_date = models.DateField(null=True, blank=True)
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_formation_events_facilitated",
    )
    completion_count = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-event_date", "title"]
        indexes = [models.Index(fields=["school", "event_type"])]

    def __str__(self) -> str:
        return self.title


class SpeakerVettingRecord(FormationTimeStampedModel):
    """Speaker/ministry/college vetting record for chapel and external engagement."""

    STATUS_CHOICES = [
        ("proposed", "Proposed"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("approved_with_conditions", "Approved with Conditions"),
        ("not_approved", "Not Approved"),
        ("completed", "Completed"),
        ("reviewed", "Reviewed"),
    ]

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="speaker_vetting_records")
    speaker_name = models.CharField(max_length=160)
    organization = models.CharField(max_length=180, blank=True, default="")
    affiliation = models.CharField(max_length=180, blank=True, default="")
    topic = models.CharField(max_length=180, blank=True, default="")
    scripture_reference = models.CharField(max_length=160, blank=True, default="")
    grade_appropriateness = models.CharField(max_length=120, blank=True, default="")
    statement_of_faith_aligned = models.BooleanField(default=False)
    parent_sensitive_content = models.BooleanField(default=False)
    references_checked = models.BooleanField(default=False)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="speaker_vetting_records_reviewed",
    )
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="proposed")
    review_notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "spiritual_life"
        ordering = ["-updated_at", "speaker_name"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return self.speaker_name
