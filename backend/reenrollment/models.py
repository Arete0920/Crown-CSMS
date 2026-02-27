"""
reenrollment/models.py

ReenrollmentSession tracks a single re-enrollment workflow lifecycle:
  draft → configured → committed → verified

Tenant-scoped via school FK (enforced in views via get_request_school_id).

State machine:
  draft       — session created; no year or fee set yet
  configured  — target year + enrollment fee set; active student list snapshotted
  committed   — billing records (BillingRun + Invoices) written atomically
  verified    — commit results read back; subsequent verify calls are read-only
"""
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from core.models import School

User = get_user_model()


class ReenrollmentSession(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_CONFIGURED = 'configured'
    STATUS_COMMITTED = 'committed'
    STATUS_VERIFIED = 'verified'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_CONFIGURED, 'Configured'),
        (STATUS_COMMITTED, 'Committed'),
        (STATUS_VERIFIED, 'Verified'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant scoping — enforced on every view lookup
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='reenrollment_sessions',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reenrollment_sessions',
    )

    # Step 1: configuration
    target_year_label = models.CharField(
        max_length=24,
        blank=True,
        default='',
        help_text='E.g. "2026-2027" — labels the BillingRun term.',
    )
    enrollment_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Per-student enrollment fee for the new year.',
    )

    # Step 3: exclusion list — list of student UUID strings (str) set by the director
    excluded_ids = models.JSONField(
        default=list,
        blank=True,
        help_text='List of households.Student UUIDs to exclude from this run.',
    )

    # Snapshot of ACTIVE students at configure time (list of dicts)
    candidates_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text='Snapshot of households.Student records eligible for re-enrollment.',
    )

    # Result of the commit step
    commit_result = models.JSONField(
        null=True,
        blank=True,
        help_text='Written by commit_session; read by verify_session.',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"ReenrollmentSession({self.school_id}, {self.target_year_label}, {self.status})"
