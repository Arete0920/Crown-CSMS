import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from core.models import School

VALID_SCHEDULE_MODES = {"SINGLE_DAY", "DAY_TEMPLATES"}


class BellSchedule(models.Model):
    """
    Persisted bell schedule for a (school, academic_year).
    One active schedule per year; commit flips siblings inactive.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school        = models.ForeignKey(School, on_delete=models.CASCADE, related_name="bell_schedules")
    academic_year = models.ForeignKey(
        "core.AcademicYear", on_delete=models.CASCADE, related_name="bell_schedules"
    )
    name          = models.CharField(max_length=100)
    schedule_mode = models.CharField(max_length=20)  # SINGLE_DAY | DAY_TEMPLATES
    is_active     = models.BooleanField(default=False)

    class Meta:
        app_label = "bell_schedule_wizard"
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "name"],
                name="uniq_bell_schedule_school_year_name",
            ),
        ]
        indexes = [models.Index(fields=["school", "is_active"])]

    def __str__(self) -> str:
        tag = "active" if self.is_active else "inactive"
        return f"BellSchedule({self.school_id}, {self.name!r}, {tag})"


class DayTemplate(models.Model):
    """
    A named day template within a BellSchedule.
    SINGLE_DAY schedules use a single template with code='DEFAULT'.
    DAY_TEMPLATES schedules use codes like A/B or MON/TUE/WED/THU/FRI.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule      = models.ForeignKey(BellSchedule, on_delete=models.CASCADE, related_name="templates")
    template_code = models.CharField(max_length=20)   # DEFAULT, A, B, MON, TUE, …
    ordering      = models.IntegerField(default=0)

    class Meta:
        app_label = "bell_schedule_wizard"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "template_code"],
                name="uniq_day_template_code",
            ),
        ]
        ordering = ["ordering"]

    def __str__(self) -> str:
        return f"DayTemplate({self.schedule_id}, {self.template_code!r})"


class PeriodBlock(models.Model):
    """
    A single time block within a DayTemplate.
    Invariants: start_time < end_time; code unique within template; no overlap.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template         = models.ForeignKey(DayTemplate, on_delete=models.CASCADE, related_name="blocks")
    code             = models.CharField(max_length=20)   # P1, P2, LUNCH, HR, BREAK
    label            = models.CharField(max_length=100)
    start_time       = models.TimeField()
    end_time         = models.TimeField()
    ordering         = models.IntegerField(default=0)
    is_instructional = models.BooleanField(default=False)
    is_lunch         = models.BooleanField(default=False)
    is_break         = models.BooleanField(default=False)

    class Meta:
        app_label = "bell_schedule_wizard"
        constraints = [
            models.UniqueConstraint(
                fields=["template", "code"],
                name="uniq_period_block_code",
            ),
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="chk_period_block_start_lt_end",
            ),
        ]
        ordering = ["ordering"]

    def __str__(self) -> str:
        return f"PeriodBlock({self.template_id}, {self.code!r}, {self.start_time}–{self.end_time})"


class BellScheduleWizardSession(models.Model):
    """
    4-state wizard session for defining a school's daily bell schedule.

    State machine:
      draft
        → configured   (POST /configure/ — name, mode, academic_year)
        → blocks_set   (POST /blocks/    — per-template period blocks)
        → committed    (POST /commit/    — materialise BellSchedule; idempotent)
        → verified     (GET  /verify/    — returns schedule snapshot)
    """

    STATUS_DRAFT      = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_BLOCKS_SET = "blocks_set"
    STATUS_COMMITTED  = "committed"
    STATUS_VERIFIED   = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,      "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_BLOCKS_SET, "Blocks Set"),
        (STATUS_COMMITTED,  "Committed"),
        (STATUS_VERIFIED,   "Verified"),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school        = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="bell_schedule_wizard_sessions"
    )
    created_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="bell_schedule_wizard_sessions_created",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="bell_schedule_wizard_sessions",
    )
    schedule_name = models.CharField(max_length=100, default="")
    schedule_mode = models.CharField(max_length=20, default="")
    # [{template_code, blocks:[{code,label,start_time,end_time,ordering,is_instructional,is_lunch,is_break}]}]
    blocks_config = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)
    status        = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "bell_schedule_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"BellScheduleWizardSession({self.school_id}, {self.schedule_name!r}, {self.status})"
