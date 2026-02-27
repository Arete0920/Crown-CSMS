from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


class StudentSpiritualProfile(models.Model):
    """One-per-student per school holistic spiritual profile."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="spiritual_profiles"
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.CASCADE, related_name="spiritual_profiles"
    )

    faith_background = models.CharField(max_length=120, blank=True, default="")
    baptized = models.BooleanField(null=True, blank=True)
    baptism_date = models.DateField(null=True, blank=True)
    spiritual_gifts = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spiritual_profiles_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("school", "student")
        indexes = [
            models.Index(fields=["school", "student"]),
        ]
        ordering = ["student__last_name", "student__first_name"]

    def __str__(self) -> str:
        return f"SpiritualProfile({self.student_id})"


class SpiritualAssessment(models.Model):
    """Worldview / discipleship assessment completed by a student."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="spiritual_assessments"
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.CASCADE, related_name="spiritual_assessments"
    )
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spiritual_assessments_administered",
    )

    assessment_title = models.CharField(max_length=180)
    assessment_date = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "student", "assessment_date"]),
        ]
        ordering = ["-assessment_date"]

    def __str__(self) -> str:
        return f"SpiritualAssessment({self.student_id}, {self.assessment_title})"


class ChapelEvent(models.Model):
    """A chapel gathering (service, guest speaker, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="chapel_events"
    )

    title = models.CharField(max_length=180)
    speaker = models.CharField(max_length=120, blank=True, default="")
    event_date = models.DateField(db_index=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=120, blank=True, default="")
    theme = models.CharField(max_length=120, blank=True, default="")
    scripture_reference = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chapel_events_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "event_date"]),
        ]
        ordering = ["-event_date"]

    def __str__(self) -> str:
        return f"ChapelEvent({self.title}, {self.event_date})"


class ChapelAttendance(models.Model):
    """Per-student attendance record for a ChapelEvent."""

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("excused", "Excused"),
        ("late", "Late"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="chapel_attendances"
    )
    event = models.ForeignKey(
        ChapelEvent, on_delete=models.CASCADE, related_name="attendances"
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.CASCADE, related_name="chapel_attendances"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="present")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chapel_attendance_recorded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("school", "event", "student")
        indexes = [
            models.Index(fields=["school", "event"]),
            models.Index(fields=["school", "student"]),
        ]

    def __str__(self) -> str:
        return f"ChapelAttendance({self.student_id}, {self.event_id}, {self.status})"


class SmallGroup(models.Model):
    """A discipleship / Bible study small group."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="small_groups"
    )

    name = models.CharField(max_length=120)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="small_groups_led",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"SmallGroup({self.name})"


class SmallGroupMember(models.Model):
    """Student membership in a SmallGroup."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="small_group_members"
    )
    group = models.ForeignKey(
        SmallGroup, on_delete=models.CASCADE, related_name="members"
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.CASCADE, related_name="small_group_memberships"
    )
    joined_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("school", "group", "student")
        indexes = [
            models.Index(fields=["school", "group"]),
        ]

    def __str__(self) -> str:
        return f"SmallGroupMember({self.student_id} @ {self.group_id})"


class SmallGroupSession(models.Model):
    """A single meeting session of a SmallGroup."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="small_group_sessions"
    )
    group = models.ForeignKey(
        SmallGroup, on_delete=models.CASCADE, related_name="sessions"
    )

    session_date = models.DateField(db_index=True)
    topic = models.CharField(max_length=180, blank=True, default="")
    scripture_reference = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "group", "session_date"]),
        ]
        ordering = ["-session_date"]

    def __str__(self) -> str:
        return f"SmallGroupSession({self.group_id}, {self.session_date})"


class SmallGroupAttendance(models.Model):
    """Per-member attendance for a SmallGroupSession."""

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("excused", "Excused"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="small_group_attendances"
    )
    session = models.ForeignKey(
        SmallGroupSession, on_delete=models.CASCADE, related_name="attendances"
    )
    member = models.ForeignKey(
        SmallGroupMember, on_delete=models.CASCADE, related_name="attendances"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="present")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("school", "session", "member")
        indexes = [
            models.Index(fields=["school", "session"]),
        ]

    def __str__(self) -> str:
        return f"SmallGroupAttendance({self.member_id}, {self.session_id}, {self.status})"


class PrayerRequest(models.Model):
    """Prayer request submitted for or by a student."""

    VISIBILITY_CHOICES = [
        ("private", "Private – pastoral only"),
        ("staff", "Staff only"),
        ("group", "Small group"),
        ("school", "School-wide"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("answered", "Answered"),
        ("closed", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="prayer_requests"
    )
    student = models.ForeignKey(
        "core.Student",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="prayer_requests",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prayer_requests_submitted",
    )

    title = models.CharField(max_length=180)
    body = models.TextField()
    visibility = models.CharField(
        max_length=16, choices=VISIBILITY_CHOICES, default="staff"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["school", "visibility"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PrayerRequest({self.title[:40]}, {self.status})"


class PastoralNote(models.Model):
    """
    Private pastoral note about a student. Access: staff / HEAD_OF_SCHOOL only.
    Never exposed to teachers, parents, or students.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="pastoral_notes"
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.CASCADE, related_name="pastoral_notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pastoral_notes_authored",
    )

    note_date = models.DateField()
    body = models.TextField()
    is_sensitive = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "student", "note_date"]),
        ]
        ordering = ["-note_date", "-created_at"]

    def __str__(self) -> str:
        return f"PastoralNote({self.student_id}, {self.note_date})"
