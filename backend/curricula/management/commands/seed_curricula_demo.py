from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from curricula.models import CurriculumMap, CurriculumMapVersion, Unit, Lesson


@dataclass(frozen=True)
class SeedLesson:
    seq: int
    title: str
    objectives: str = ""
    resources: str = ""


@dataclass(frozen=True)
class SeedUnit:
    seq: int
    title: str
    overview: str
    lessons: tuple[SeedLesson, ...]


@dataclass(frozen=True)
class SeedMap:
    title: str
    grade_band: str
    subject: str
    units: tuple[SeedUnit, ...]


DEMO_MAPS: tuple[SeedMap, ...] = (
    SeedMap(
        title="Bible 9: Foundations of Faith",
        grade_band="9",
        subject="Bible",
        units=(
            SeedUnit(
                seq=1,
                title="Creation, Fall, Redemption",
                overview="Big-picture storyline of Scripture: creation, fall, redemption, restoration.",
                lessons=(
                    SeedLesson(1, "Why worldview matters", "Define worldview; connect beliefs to choices.", "Slides, discussion questions"),
                    SeedLesson(2, "Creation and dignity", "Imago Dei; purpose and value.", "Genesis 1-2"),
                    SeedLesson(3, "The fall and brokenness", "Sin and its effects; hope begins.", "Genesis 3"),
                ),
            ),
            SeedUnit(
                seq=2,
                title="Who Jesus Is",
                overview="Person and work of Christ; why it matters for daily life.",
                lessons=(
                    SeedLesson(1, "Names and titles of Christ", "Explore key titles and meanings.", "Gospels"),
                    SeedLesson(2, "The cross", "Substitution, forgiveness, reconciliation.", "Romans 5"),
                    SeedLesson(3, "Resurrection and mission", "Hope and purpose; Great Commission.", "Matthew 28"),
                ),
            ),
        ),
    ),
    SeedMap(
        title="English 7: Composition & Reading",
        grade_band="7",
        subject="English",
        units=(
            SeedUnit(
                seq=1,
                title="Paragraph Power",
                overview="Topic sentences, supporting details, transitions.",
                lessons=(
                    SeedLesson(1, "What makes a strong paragraph", "Identify topic/supporting sentences.", "Model paragraphs"),
                    SeedLesson(2, "Transitions that actually work", "Use transitions to improve flow.", "Transition list"),
                ),
            ),
            SeedUnit(
                seq=2,
                title="Narrative Writing",
                overview="Characters, conflict, setting, pacing.",
                lessons=(
                    SeedLesson(1, "Hook the reader", "Write openings with a clear voice.", "Mentor texts"),
                    SeedLesson(2, "Show, don't tell", "Use sensory detail and action.", "Revision checklist"),
                ),
            ),
        ),
    ),
    SeedMap(
        title="Algebra I: Core Skills",
        grade_band="9-10",
        subject="Math",
        units=(
            SeedUnit(
                seq=1,
                title="Expressions & Equations",
                overview="Variables, simplifying, solving one-step and multi-step equations.",
                lessons=(
                    SeedLesson(1, "Simplify expressions", "Combine like terms; distributive property.", "Practice set A"),
                    SeedLesson(2, "Solve equations", "One-step and two-step equations.", "Practice set B"),
                ),
            ),
            SeedUnit(
                seq=2,
                title="Linear Functions",
                overview="Slope, intercepts, graphing, interpreting models.",
                lessons=(
                    SeedLesson(1, "Slope as rate of change", "Compute slope from points/tables.", "Graph paper"),
                    SeedLesson(2, "Slope-intercept form", "Graph y=mx+b; interpret parameters.", "Desmos (optional)"),
                ),
            ),
        ),
    ),
)


class Command(BaseCommand):
    help = "Seed curricula demo data for a given school_id (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            required=True,
            help="UUID of the tenant school to seed (e.g., from DEMO school record).",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="If set, deletes existing curricula rows for this school before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        school_id = uuid.UUID(str(opts["school_id"]))
        wipe = bool(opts["wipe"])

        if wipe:
            Lesson.objects.filter(school_id=school_id).delete()
            Unit.objects.filter(school_id=school_id).delete()
            CurriculumMapVersion.objects.filter(school_id=school_id).delete()
            CurriculumMap.objects.filter(school_id=school_id).delete()

        created_maps = 0
        created_versions = 0
        created_units = 0
        created_lessons = 0

        for m in DEMO_MAPS:
            cmap, cmap_created = CurriculumMap.objects.get_or_create(
                school_id=school_id,
                title=m.title,
                defaults={
                    "grade_band": m.grade_band,
                    "subject": m.subject,
                },
            )
            if cmap_created:
                created_maps += 1

            version, version_created = CurriculumMapVersion.objects.get_or_create(
                school_id=school_id,
                curriculum_map=cmap,
                version_number=1,
                defaults={
                    "status": CurriculumMapVersion.Status.PUBLISHED,
                    "change_summary": "Initial demo curriculum edition.",
                },
            )
            if version_created:
                created_versions += 1

            for u in m.units:
                unit, unit_created = Unit.objects.get_or_create(
                    school_id=school_id,
                    curriculum_map=cmap,
                    curriculum_version=version,
                    sequence=u.seq,
                    defaults={
                        "title": u.title,
                        "overview": u.overview,
                    },
                )
                if unit_created:
                    created_units += 1

                for l in u.lessons:
                    _, lesson_created = Lesson.objects.get_or_create(
                        school_id=school_id,
                        unit=unit,
                        sequence=l.seq,
                        defaults={
                            "title": l.title,
                            "objectives": l.objectives,
                            "resources": l.resources,
                        },
                    )
                    if lesson_created:
                        created_lessons += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete for school_id={school_id}. "
                f"created: maps={created_maps}, versions={created_versions}, "
                f"units={created_units}, lessons={created_lessons}"
            )
        )
