"""
onboarding/models_tasks.py

OnboardingTask — per-school checklist items that must be completed before
a school can be activated for live billing.

HelpArticle / Solomon* — contextual knowledge-base content, categories,
audiences, and playbooks used by the Solomon support surface.
"""
from __future__ import annotations

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


class SolomonCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class SolomonTopic(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SolomonAudience(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    role_code = models.CharField(max_length=64, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HelpArticle(models.Model):
    """Contextual help content surfaced via HelpTooltip and the Solomon panel."""

    TYPE_GUIDE = "guide"
    TYPE_CONTEXTUAL = "contextual"
    TYPE_FAQ = "faq"
    TYPE_MIGRATION = "migration"
    TYPE_CHOICES = [
        (TYPE_GUIDE, "Guide"),
        (TYPE_CONTEXTUAL, "Contextual"),
        (TYPE_FAQ, "FAQ"),
        (TYPE_MIGRATION, "Migration"),
    ]

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_AUTHENTICATED = "authenticated"
    VISIBILITY_STAFF = "staff"
    VISIBILITY_ADMIN = "admin"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_AUTHENTICATED, "Authenticated"),
        (VISIBILITY_STAFF, "Staff"),
        (VISIBILITY_ADMIN, "Admin"),
    ]

    STATE_DRAFT = "draft"
    STATE_PUBLISHED = "published"
    STATE_ARCHIVED = "archived"
    STATE_CHOICES = [
        (STATE_DRAFT, "Draft"),
        (STATE_PUBLISHED, "Published"),
        (STATE_ARCHIVED, "Archived"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True, default="")
    content = models.TextField()
    module = models.CharField(max_length=100, db_index=True)
    article_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GUIDE)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_PUBLISHED)
    category = models.ForeignKey(
        SolomonCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles",
    )
    topics = models.ManyToManyField(SolomonTopic, blank=True, related_name="articles")
    audiences = models.ManyToManyField(SolomonAudience, blank=True, related_name="articles")
    route_path = models.CharField(max_length=200, blank=True, default="")
    published = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "sort_order", "title"]

    def __str__(self):
        return f"HelpArticle({self.slug})"


class SolomonPlaybook(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True, default="")
    module = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(
        SolomonCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="playbooks",
    )
    visibility = models.CharField(max_length=20, choices=HelpArticle.VISIBILITY_CHOICES, default=HelpArticle.VISIBILITY_PUBLIC)
    state = models.CharField(max_length=20, choices=HelpArticle.STATE_CHOICES, default=HelpArticle.STATE_PUBLISHED)
    route_path = models.CharField(max_length=200, blank=True, default="")
    checklist = models.JSONField(default=list, blank=True)
    audiences = models.ManyToManyField(SolomonAudience, blank=True, related_name="playbooks")
    sort_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "sort_order", "title"]

    def __str__(self):
        return f"SolomonPlaybook({self.slug})"


class SolomonRouteContext(models.Model):
    module = models.CharField(max_length=100, db_index=True)
    route_path = models.CharField(max_length=200, db_index=True)
    context_key = models.CharField(max_length=100, blank=True, default="")
    help_article = models.ForeignKey(
        HelpArticle,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="route_contexts",
    )
    playbook = models.ForeignKey(
        SolomonPlaybook,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="route_contexts",
    )
    audience = models.ForeignKey(
        SolomonAudience,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="route_contexts",
    )
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ["module", "route_path", "priority"]

    def __str__(self):
        return f"SolomonRouteContext({self.module}, {self.route_path}, {self.context_key})"


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
