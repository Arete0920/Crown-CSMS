"""Append-only, default-off Diadem evidence reviews for issue #595.

Source-only migration file. Do not apply without a separate authorized
migration rehearsal and rollback/restore checkpoint.
"""
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def _common():
    # Each CreateModel must own distinct Django Field objects.
    return [
    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
    ("created_at", models.DateTimeField(auto_now_add=True)),
    ("updated_at", models.DateTimeField(auto_now=True)),
    ("reviewed_at", models.DateTimeField(default=django.utils.timezone.now)),
    ("effective_from", models.DateTimeField()),
    ("effective_until", models.DateTimeField()),
    ("source_authority", models.CharField(max_length=160)),
    ("source_reference", models.CharField(max_length=255)),
    ("request_key", models.UUIDField()),
    ("school", models.ForeignKey(to="core.school", on_delete=django.db.models.deletion.PROTECT)),
]


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0014_legacy_insert_defaults"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DaycareStaffQualificationReview",
            fields=_common() + [
                ("qualification_code", models.CharField(max_length=64)),
                ("decision", models.CharField(max_length=12, choices=[
                    ("VERIFIED", "External evidence reviewed"),
                    ("REJECTED", "Evidence rejected"),
                    ("REVOKED", "Previous review revoked"),
                ])),
                ("site", models.ForeignKey(
                    to="aftercare.daycaresite", on_delete=django.db.models.deletion.PROTECT,
                    related_name="staff_qualification_reviews",
                )),
                ("staff", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                    related_name="daycare_qualification_reviews",
                )),
                ("reviewed_by", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                    related_name="+",
                )),
                ("supersedes", models.OneToOneField(
                    to="aftercare.daycarestaffqualificationreview", null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT, related_name="successor",
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=["school", "request_key"], name="dia_qual_review_retry_uq",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["school", "site", "staff"], name="dia_qual_staff_scope_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DaycareRoomPolicyReview",
            fields=_common() + [
                ("jurisdiction", models.CharField(max_length=16)),
                ("policy_version", models.CharField(max_length=64)),
                ("facility_license_reference", models.CharField(max_length=160)),
                ("age_min_months", models.PositiveIntegerField()),
                ("age_max_months", models.PositiveIntegerField()),
                ("licensed_capacity", models.PositiveIntegerField()),
                ("max_group_size", models.PositiveIntegerField()),
                ("max_children_per_staff", models.PositiveIntegerField()),
                ("decision", models.CharField(max_length=12, choices=[
                    ("APPROVED", "Policy evidence reviewed"),
                    ("REJECTED", "Policy evidence rejected"),
                    ("REVOKED", "Previous review revoked"),
                ])),
                ("site", models.ForeignKey(
                    to="aftercare.daycaresite", on_delete=django.db.models.deletion.PROTECT,
                    related_name="room_policy_reviews",
                )),
                ("room", models.ForeignKey(
                    to="aftercare.daycareroom", on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_policy_reviews",
                )),
                ("reviewed_by", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                    related_name="+",
                )),
                ("supersedes", models.OneToOneField(
                    to="aftercare.daycareroompolicyreview", null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT, related_name="successor",
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=["school", "request_key"], name="dia_policy_review_retry_uq",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(age_max_months__gte=models.F("age_min_months")),
                        name="dia_policy_age_range_ck",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(licensed_capacity__gt=0, max_group_size__gt=0,
                                           max_children_per_staff__gt=0),
                        name="dia_policy_positive_ck",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["school", "site", "room"], name="dia_policy_room_scope_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DaycareStaffAssignmentReview",
            fields=_common() + [
                ("decision", models.CharField(max_length=12, choices=[
                    ("APPROVED", "Planning assignment reviewed"),
                    ("REJECTED", "Planning assignment rejected"),
                    ("REVOKED", "Previous planning review revoked"),
                ])),
                ("proposal", models.ForeignKey(
                    to="aftercare.daycareroomstaffcoverage",
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="planning_approval_reviews",
                )),
                ("qualification_review", models.ForeignKey(
                    to="aftercare.daycarestaffqualificationreview",
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="planning_assignment_reviews",
                )),
                ("room_policy_review", models.ForeignKey(
                    to="aftercare.daycareroompolicyreview",
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="planning_assignment_reviews",
                )),
                ("reviewed_by", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                    related_name="+",
                )),
                ("supersedes", models.OneToOneField(
                    to="aftercare.daycarestaffassignmentreview", null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT, related_name="successor",
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=["school", "request_key"], name="dia_assign_review_retry_uq",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["school", "proposal"], name="dia_assign_prop_scope_idx",
                    ),
                ],
            },
        ),
    ]
