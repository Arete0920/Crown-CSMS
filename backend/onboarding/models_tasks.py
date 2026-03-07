"""
onboarding/models_tasks.py

OnboardingTask — per-school checklist items that must be completed before
a school can be activated for live billing.

HelpArticle — contextual in-app help content, scoped to module slug.
"""
from django.db import models
from core.models import School


DEFAULT_TASKS = [
    "Configure School Profile",
    "Upload Students",
    "Set Tuition Plans",
    "Configure Financial Aid",
    "Invite Teachers",
    "Activate Parent Portal",
]


class OnboardingTask(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETE = "complete"
    TASK_STATUS = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETE, "Complete"),
    ]

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="onboarding_tasks",
    )
    task_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default=STATUS_PENDING)
    order = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("school", "task_name")

    def __str__(self):
        return f"OnboardingTask({self.school_id}, {self.task_name}, {self.status})"


def seed_onboarding_tasks(school: School) -> list[OnboardingTask]:
    """Idempotent — safe to call multiple times; skips tasks that already exist."""
    created = []
    for i, name in enumerate(DEFAULT_TASKS):
        task, was_created = OnboardingTask.objects.get_or_create(
            school=school,
            task_name=name,
            defaults={"status": OnboardingTask.STATUS_PENDING, "order": i},
        )
        if was_created:
            created.append(task)
    return created


def can_activate_school(school: School) -> bool:
    """Return True only when every onboarding task is complete.
    Used as a gate before enabling live billing."""
    tasks = OnboardingTask.objects.filter(school=school)
    if not tasks.exists():
        return False
    return not tasks.filter(status=OnboardingTask.STATUS_PENDING).exists()


class HelpArticle(models.Model):
    """Contextual help content surfaced via HelpTooltip and help panel."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    module = models.CharField(max_length=100, db_index=True)
    published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "title"]

    def __str__(self):
        return f"HelpArticle({self.slug})"
