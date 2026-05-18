"""
SOLOMON Phase 2 core knowledge models.

Approved by ALR-1:
- Core knowledge/resource structure only
- Additive Solomon app models only
- No live module wiring
- No curriculum/scripture/devotional/publisher/AI/Microsoft integration
"""

from __future__ import annotations

from django.db import models


class SolomonLifecycle(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class SolomonVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    AUTHENTICATED = "authenticated", "Authenticated"
    STAFF = "staff", "Staff"
    ADMIN = "admin", "Admin"


class SolomonScope(models.TextChoices):
    GLOBAL = "global", "Global"
    ORGANIZATION = "organization", "Organization"
    SCHOOL = "school", "School"
    ROLE = "role", "Role"
    AUDIENCE = "audience", "Audience"


class SolomonResourceType(models.TextChoices):
    ARTICLE = "article", "Article"
    POLICY = "policy", "Policy"
    GUIDE = "guide", "Guide"
    TEMPLATE = "template", "Template"
    PLAYBOOK = "playbook", "Playbook"
    EXTERNAL = "external", "External"


class SolomonCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class SolomonTopic(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SolomonAudience(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    role_code = models.CharField(max_length=64, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SolomonResource(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    resource_type = models.CharField(
        max_length=20,
        choices=SolomonResourceType.choices,
        default=SolomonResourceType.ARTICLE,
    )
    status = models.CharField(
        max_length=20,
        choices=SolomonLifecycle.choices,
        default=SolomonLifecycle.DRAFT,
    )
    visibility = models.CharField(
        max_length=20,
        choices=SolomonVisibility.choices,
        default=SolomonVisibility.AUTHENTICATED,
    )
    scope = models.CharField(
        max_length=20,
        choices=SolomonScope.choices,
        default=SolomonScope.SCHOOL,
    )
    category = models.ForeignKey(
        SolomonCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resources",
    )
    topics = models.ManyToManyField(SolomonTopic, blank=True, related_name="resources")
    audiences = models.ManyToManyField(SolomonAudience, blank=True, related_name="resources")
    owner = models.CharField(max_length=200, blank=True, default="")
    approver = models.CharField(max_length=200, blank=True, default="")
    review_date = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=40, blank=True, default="1.0")
    license_type = models.CharField(max_length=80, blank=True, default="")
    source_url = models.URLField(blank=True, default="")
    module = models.CharField(max_length=100, blank=True, default="", db_index=True)
    route_path = models.CharField(max_length=200, blank=True, default="", db_index=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "sort_order", "title"]

    def __str__(self) -> str:
        return f"SolomonResource({self.slug})"


class SolomonResourceVersion(models.Model):
    resource = models.ForeignKey(
        SolomonResource,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default="")
    summary = models.TextField(blank=True, default="")
    change_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["resource", "-created_at"]

    def __str__(self) -> str:
        return f"SolomonResourceVersion({self.resource.slug}, {self.version})"


class SolomonPlaybook(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True, default="")
    module = models.CharField(max_length=100, blank=True, default="", db_index=True)
    category = models.ForeignKey(
        SolomonCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="playbooks",
    )
    visibility = models.CharField(
        max_length=20,
        choices=SolomonVisibility.choices,
        default=SolomonVisibility.AUTHENTICATED,
    )
    status = models.CharField(
        max_length=20,
        choices=SolomonLifecycle.choices,
        default=SolomonLifecycle.DRAFT,
    )
    route_path = models.CharField(max_length=200, blank=True, default="", db_index=True)
    checklist = models.JSONField(default=list, blank=True)
    audiences = models.ManyToManyField(SolomonAudience, blank=True, related_name="playbooks")
    owner = models.CharField(max_length=200, blank=True, default="")
    approver = models.CharField(max_length=200, blank=True, default="")
    review_date = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=40, blank=True, default="1.0")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "sort_order", "title"]

    def __str__(self) -> str:
        return f"SolomonPlaybook({self.slug})"


class SolomonContextRule(models.Model):
    module = models.CharField(max_length=100, db_index=True)
    route_path = models.CharField(max_length=200, db_index=True)
    context_key = models.CharField(max_length=100, blank=True, default="")
    resource = models.ForeignKey(
        SolomonResource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="context_rules",
    )
    playbook = models.ForeignKey(
        SolomonPlaybook,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="context_rules",
    )
    audience = models.ForeignKey(
        SolomonAudience,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="context_rules",
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "route_path", "priority"]

    def __str__(self) -> str:
        return f"SolomonContextRule({self.module}, {self.route_path}, {self.context_key})"
