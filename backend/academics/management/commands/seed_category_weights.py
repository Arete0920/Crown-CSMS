"""
Seed AssignmentCategory objects with realistic weights for demo purposes.

Creates 4 categories per section:
- Homework (20%)
- Quizzes (30%)
- Projects (25%)
- Exams (25%)

Idempotent: Uses get_or_create so can be re-run safely.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import School
from academics.models import Section, AssignmentCategory


@dataclass(frozen=True)
class CategorySpec:
    name: str
    weight_percent: Decimal
    sort_order: int


DEFAULT_CATEGORIES: tuple[CategorySpec, ...] = (
    CategorySpec("Homework", Decimal("20.00"), 1),
    CategorySpec("Quizzes", Decimal("30.00"), 2),
    CategorySpec("Projects", Decimal("25.00"), 3),
    CategorySpec("Exams", Decimal("25.00"), 4),
)


class Command(BaseCommand):
    help = "Seed AssignmentCategory objects with demo weights for sections in school. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True, help="UUID of the tenant school to seed.")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be created without creating.")
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing AssignmentCategory rows for this school before seeding."
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        school_id = uuid.UUID(str(opts["school_id"]))
        dry_run = bool(opts.get("dry_run", False))
        wipe = bool(opts.get("wipe", False))

        # Validate school exists
        if not School.objects.filter(pk=school_id).exists():
            raise SystemExit(f"School not found: {school_id}")

        if wipe and not dry_run:
            deleted, _ = AssignmentCategory.objects.filter(school_id=school_id).delete()
            self.stdout.write(
                self.style.WARNING(f"WIPED AssignmentCategory rows for school_id={school_id}: deleted={deleted}")
            )

        # Only seed sections that have enrollments (roster) for realism
        sections_qs = (
            Section.objects.filter(school_id=school_id)
            .annotate(roster_count=Count("enrollments", distinct=True))
            .filter(roster_count__gt=0)
            .order_by("id")
        )

        created_count = 0
        skipped_count = 0
        scanned_sections = 0

        for section in sections_qs:
            scanned_sections += 1

            for spec in DEFAULT_CATEGORIES:
                if dry_run:
                    exists = AssignmentCategory.objects.filter(
                        school_id=school_id,
                        section=section,
                        name=spec.name
                    ).exists()
                    
                    if exists:
                        self.stdout.write(f"[DRY-RUN] SKIP: Section {section.id} - {spec.name} (exists)")
                        skipped_count += 1
                    else:
                        self.stdout.write(
                            f"[DRY-RUN] CREATE: Section {section.id} - {spec.name} "
                            f"({spec.weight_percent}%, order={spec.sort_order})"
                        )
                        created_count += 1
                else:
                    obj, was_created = AssignmentCategory.objects.get_or_create(
                        school_id=school_id,
                        section=section,
                        name=spec.name,
                        defaults={
                            "weight_percent": spec.weight_percent,
                            "sort_order": spec.sort_order,
                            "is_active": True,
                        }
                    )
                    if was_created:
                        created_count += 1
                    else:
                        skipped_count += 1

        mode = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}Seed complete for school_id={school_id}. "
                f"sections_scanned={scanned_sections}, "
                f"categories_created={created_count}, "
                f"categories_skipped={skipped_count}"
            )
        )
