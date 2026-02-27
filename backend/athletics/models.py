# backend/athletics/models.py
from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import School, Student  # noqa: F401


class Sport(models.Model):
    """Catalog of sports per school."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="sports")
    name = models.CharField(max_length=120)
    gender = models.CharField(max_length=16, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("school", "name", "gender")
        indexes = [models.Index(fields=["school", "is_active"])]

    def __str__(self) -> str:
        g = f" ({self.gender})" if self.gender else ""
        return f"{self.name}{g}"


class Season(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)

    class Meta:
        unique_together = ("school", "name")
        indexes = [models.Index(fields=["school", "start_date"])]

    def __str__(self) -> str:
        return self.name


class Team(models.Model):
    LEVEL_CHOICES = [
        ("V", "Varsity"),
        ("JV", "Junior Varsity"),
        ("MS", "Middle School"),
        ("ES", "Elementary"),
        ("CLUB", "Club"),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="teams")
    sport = models.ForeignKey(Sport, on_delete=models.PROTECT, related_name="teams")
    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="teams")
    level = models.CharField(max_length=8, choices=LEVEL_CHOICES, default="V")
    display_name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    participation_fee_cents = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        indexes = [
            models.Index(fields=["school", "season"]),
            models.Index(fields=["school", "sport"]),
        ]

    def __str__(self) -> str:
        return self.display_name


class TeamCoach(models.Model):
    """Coach assignment."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="team_coaches")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="coaches")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="coaching_assignments",
    )
    is_head_coach = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("team", "user")
        indexes = [models.Index(fields=["school", "team"])]


class TeamRoster(models.Model):
    """Student roster membership."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="team_rosters")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="roster")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="team_memberships")
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("team", "student")
        indexes = [
            models.Index(fields=["school", "team"]),
            models.Index(fields=["school", "student"]),
        ]

    @property
    def is_active(self) -> bool:
        return self.left_at is None


class Facility(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="facilities")
    name = models.CharField(max_length=160)
    address = models.CharField(max_length=240, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("school", "name")


class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ("PRACTICE", "Practice"),
        ("GAME", "Game"),
        ("TRYOUT", "Tryout"),
        ("MEETING", "Meeting"),
        ("OTHER", "Other"),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="athletic_events")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="events")
    facility = models.ForeignKey(
        Facility, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    event_type = models.CharField(max_length=16, choices=EVENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    opponent = models.CharField(max_length=200, blank=True, default="")
    is_home = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "starts_at"]),
            models.Index(fields=["school", "team", "starts_at"]),
        ]


class AthleteClearance(models.Model):
    """Track basic clearance checklist per student."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="athlete_clearances")
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="athlete_clearance")
    consent_signed_at = models.DateTimeField(null=True, blank=True)
    physical_expires_on = models.DateField(null=True, blank=True)
    insurance_on_file = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school"])]

    def physical_is_valid(self) -> bool:
        if not self.physical_expires_on:
            return False
        return timezone.localdate() <= self.physical_expires_on


class AthleteEligibility(models.Model):
    """Cached snapshot of eligibility for a given team/student."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="athlete_eligibility")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="eligibility")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="eligibility")
    is_medically_cleared = models.BooleanField(default=False)
    is_academically_eligible = models.BooleanField(default=False)
    is_behaviorally_eligible = models.BooleanField(default=False)
    is_attendance_eligible = models.BooleanField(default=False)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("team", "student")
        indexes = [
            models.Index(fields=["school", "team"]),
            models.Index(fields=["school", "student"]),
        ]

    @property
    def is_eligible(self) -> bool:
        return (
            self.is_medically_cleared
            and self.is_academically_eligible
            and self.is_behaviorally_eligible
            and self.is_attendance_eligible
        )
