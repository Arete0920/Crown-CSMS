from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import School
from academics.models import Section
from gradebook.models import GradeEntry


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedAssignment:
    name: str
    points_possible: int


DEFAULT_ASSIGNMENTS: tuple[SeedAssignment, ...] = (
    # Quizzes (low stakes)
    SeedAssignment("Quiz 1", 20),
    SeedAssignment("Quiz 2", 20),
    SeedAssignment("Quiz 3", 20),
    SeedAssignment("Quiz 4", 20),

    # Homework (very low stakes)
    SeedAssignment("Homework 1", 10),
    SeedAssignment("Homework 2", 10),
    SeedAssignment("Homework 3", 10),
    SeedAssignment("Homework 4", 10),

    # Major items
    SeedAssignment("Project 1", 50),
    SeedAssignment("Project 2", 50),
    SeedAssignment("Midterm Exam", 100),
    SeedAssignment("Final Exam", 100),
)


def _missing_prob(name: str) -> float:
    """Probability that a student misses (has no grade) for this assignment."""
    n = name.lower()
    if "homework" in n:
        return 0.15
    if "quiz" in n:
        return 0.10
    if "project" in n:
        return 0.05
    if "midterm" in n or "final" in n or "exam" in n:
        return 0.03
    return 0.07


def _student_ids_for_section(section: Section) -> list[uuid.UUID]:
    """
    Prefer real roster: Section.enrollments -> student_id (based on your existing gradebook views).
    Fall back to any existing grade entries if enrollments aren't present.
    """
    # Attempt to use enrollments if the relation exists
    if hasattr(section, "enrollments"):
        try:
            qs = section.enrollments.all()
            # enrollment model might be Enrollment(student=...) or Enrollment(student_id=...)
            if qs.model and hasattr(qs.model, "student_id"):
                return list(qs.values_list("student_id", flat=True))
            if qs.model and hasattr(qs.model, "student"):
                return list(qs.values_list("student__id", flat=True))
        except Exception:
            logger.exception("seed_gradebook_demo: failed reading section enrollments")

    # Fallback: existing grade entries
    return list(
        GradeEntry.objects.filter(section_id=section.id).values_list("student_id", flat=True).distinct()
    )


def _score(rng: random.Random, points_possible: int, assignment_name: str) -> int | None:
    """Generate a score with realistic missingness. Returns None if student missed assignment."""
    # Check missingness first
    if rng.random() < _missing_prob(assignment_name):
        return None
    # Otherwise generate score: 60%–100% range
    low = int(points_possible * 0.6)
    return round(rng.uniform(low, points_possible), 2)


class Command(BaseCommand):
    help = "Seed Gradebook demo data (GradeEntry rows) for a given school_id. Idempotent and rerunnable."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True, help="UUID of the tenant school to seed.")
        parser.add_argument(
            "--sections",
            default="",
            help="Optional comma-separated section UUIDs to seed (otherwise seeds all accessible sections with roster).",
        )
        parser.add_argument("--wipe", action="store_true", help="Delete existing GradeEntry rows for this school before seeding.")
        parser.add_argument("--per-section", type=int, default=5, help="How many assignments to seed per section (default 5).")
        parser.add_argument("--seed", type=int, default=2026, help="Random seed for repeatable scores (default 2026).")

    @transaction.atomic
    def handle(self, *args, **opts):
        seed_value = int(opts["seed"])
        rng = random.Random(seed_value)

        school_id = uuid.UUID(str(opts["school_id"]))
        wipe = bool(opts["wipe"])
        per_section = int(opts["per_section"])

        # Validate school exists (helps catch wrong IDs fast)
        if not School.objects.filter(pk=school_id).exists():
            raise SystemExit(f"School not found: {school_id}")

        if wipe:
            deleted, _ = GradeEntry.objects.filter(school_id=school_id).delete()
            self.stdout.write(self.style.WARNING(f"WIPED GradeEntry rows for school_id={school_id}: deleted={deleted}"))

        # Section selection
        section_ids_raw = str(opts["sections"]).strip()
        if section_ids_raw:
            section_ids = [uuid.UUID(x.strip()) for x in section_ids_raw.split(",") if x.strip()]
            sections_qs = Section.objects.filter(school_id=school_id, id__in=section_ids)
        else:
            # Only seed sections that have enrollments (roster) if possible
            sections_qs = (
                Section.objects.filter(school_id=school_id)
                .annotate(roster_count=Count("enrollments", distinct=True))
                .filter(roster_count__gt=0)
                .order_by("id")
            )

        created = 0
        skipped = 0
        scanned_sections = 0

        for section in sections_qs:
            scanned_sections += 1

            student_ids = _student_ids_for_section(section)
            if not student_ids:
                # If a section has no roster, skip (prevents empty noise)
                continue

            assignments = DEFAULT_ASSIGNMENTS[:per_section]

            for student_id in student_ids:
                for a in assignments:
                    points_earned = _score(rng, a.points_possible, a.name)

                    obj, was_created = GradeEntry.objects.get_or_create(
                        school_id=school_id,
                        section_id=section.id,
                        student_id=student_id,
                        assignment_name=a.name,
                        defaults={
                            "points_earned": points_earned,
                            "points_possible": a.points_possible,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete for school_id={school_id}. "
                f"sections_scanned={scanned_sections}, "
                f"entries_created={created}, "
                f"entries_skipped={skipped}"
            )
        )
