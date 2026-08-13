from __future__ import annotations

import json
from collections import defaultdict
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.models import Course as AcademicCourse
from academics.models import Section as AcademicSection
from academics.models import TeacherAssignment
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, Staff
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import Section as LegacySection
from section_scheduler_wizard.models import SectionPlacement


class Command(BaseCommand):
    help = (
        "Plan or apply data-preserving reconciliation from legacy "
        "section_scheduler_wizard.Section rows into canonical SectionPlacement rows. "
        "Dry-run is the default; --apply writes only when every selected legacy row maps cleanly."
    )

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--academic-year-id", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Raise CommandError when any row cannot be reconciled.",
        )

    def handle(self, *args, **options):
        try:
            school_id = UUID(str(options["school_id"]))
            academic_year_id = UUID(str(options["academic_year_id"]))
        except (TypeError, ValueError, AttributeError) as exc:
            raise CommandError("school-id and academic-year-id must be UUIDs") from exc

        academic_year = AcademicYear.objects.filter(
            id=academic_year_id,
            school_id=school_id,
        ).first()
        if not academic_year:
            raise CommandError("AcademicYear not found for the requested school")

        legacy_rows = list(
            LegacySection.objects.filter(
                school_id=school_id,
                academic_year_id=academic_year_id,
            )
            .select_related("course", "teacher", "room")
            .order_by("term_code", "section_code", "id")
        )

        active_schedule = BellSchedule.objects.filter(
            school_id=school_id,
            academic_year_id=academic_year_id,
            is_active=True,
        ).first()

        errors = []
        warnings = []
        plan = []
        planned_room_slots = set()
        planned_sections = set()

        if legacy_rows and not active_schedule:
            errors.append(
                {
                    "kind": "missing_active_bell_schedule",
                    "academic_year_id": str(academic_year_id),
                }
            )

        for legacy in legacy_rows:
            row_errors = []
            academic_course = AcademicCourse.objects.filter(
                school_id=school_id,
                code__iexact=legacy.course.code,
            ).first()
            if not academic_course:
                row_errors.append("canonical_course_missing")
                candidates = []
            else:
                candidates = list(
                    AcademicSection.objects.filter(
                        school_id=school_id,
                        course=academic_course,
                        term_ref__academic_year_id=academic_year_id,
                        term__iexact=legacy.term_code,
                    ).order_by("id")
                )
                if len(candidates) == 0:
                    row_errors.append("canonical_section_missing")
                elif len(candidates) > 1:
                    row_errors.append("canonical_section_ambiguous")

            canonical_section = candidates[0] if len(candidates) == 1 else None

            day_template = None
            period_block = None
            if active_schedule:
                day_template = DayTemplate.objects.filter(
                    schedule=active_schedule,
                    template_code__iexact=legacy.template_code,
                ).first()
                if not day_template:
                    row_errors.append("day_template_missing")
                else:
                    period_block = PeriodBlock.objects.filter(
                        template=day_template,
                        code__iexact=legacy.block_code,
                    ).first()
                    if not period_block:
                        row_errors.append("period_block_missing")

            room = None
            if legacy.room_id:
                room = Room.objects.filter(
                    id=legacy.room_id,
                    school_id=school_id,
                ).first()
                if not room:
                    row_errors.append("room_missing_or_cross_tenant")

            if canonical_section and legacy.teacher_id:
                canonical_staff = Staff.objects.filter(
                    school_id=school_id,
                    email__iexact=legacy.teacher.email,
                ).first()
                if not canonical_staff:
                    row_errors.append("canonical_staff_missing")
                elif not TeacherAssignment.objects.filter(
                    school_id=school_id,
                    section=canonical_section,
                    staff=canonical_staff,
                ).exists():
                    row_errors.append("teacher_assignment_mismatch")

            if canonical_section and canonical_section.id in planned_sections:
                row_errors.append("multiple_legacy_rows_map_to_one_canonical_section")

            if (
                legacy.is_active
                and room
                and day_template
                and period_block
            ):
                room_slot = (room.id, day_template.id, period_block.id)
                if room_slot in planned_room_slots:
                    row_errors.append("planned_room_collision")
                if SectionPlacement.objects.filter(
                    school_id=school_id,
                    academic_year_id=academic_year_id,
                    room=room,
                    day_template=day_template,
                    period_block=period_block,
                    is_active=True,
                ).exclude(section=canonical_section).exists():
                    row_errors.append("existing_room_collision")

            if row_errors:
                errors.append(
                    {
                        "legacy_section_id": str(legacy.id),
                        "legacy_section_code": legacy.section_code,
                        "errors": row_errors,
                    }
                )
                continue

            if canonical_section:
                planned_sections.add(canonical_section.id)
            if legacy.is_active and room:
                planned_room_slots.add((room.id, day_template.id, period_block.id))

            if not legacy.teacher_id and canonical_section:
                assignment_count = TeacherAssignment.objects.filter(
                    school_id=school_id,
                    section=canonical_section,
                ).count()
                if assignment_count:
                    warnings.append(
                        {
                            "legacy_section_id": str(legacy.id),
                            "warning": "legacy_teacher_empty_but_canonical_staffing_present",
                            "canonical_assignment_count": assignment_count,
                        }
                    )

            plan.append(
                {
                    "legacy_section_id": str(legacy.id),
                    "legacy_section_code": legacy.section_code,
                    "canonical_section_id": str(canonical_section.id),
                    "room_id": str(room.id) if room else None,
                    "day_template_id": str(day_template.id),
                    "period_block_id": str(period_block.id),
                    "is_active": legacy.is_active,
                }
            )

        summary = {
            "mode": "apply" if options["apply"] else "dry-run",
            "school_id": str(school_id),
            "academic_year_id": str(academic_year_id),
            "legacy_rows": len(legacy_rows),
            "planned": len(plan),
            "errors": errors,
            "warnings": warnings,
            "writes": 0,
            "deletes": 0,
        }

        # Apply is intentionally all-or-nothing. There is no partial copy mode.
        if options["apply"] and errors:
            raise CommandError(json.dumps(summary, sort_keys=True))

        if options["apply"]:
            with transaction.atomic():
                AcademicYear.objects.select_for_update().get(
                    id=academic_year_id,
                    school_id=school_id,
                )
                writes = 0
                for item in plan:
                    _, created = SectionPlacement.objects.update_or_create(
                        section_id=item["canonical_section_id"],
                        defaults={
                            "school_id": school_id,
                            "academic_year_id": academic_year_id,
                            "room_id": item["room_id"],
                            "day_template_id": item["day_template_id"],
                            "period_block_id": item["period_block_id"],
                            "is_active": item["is_active"],
                        },
                    )
                    writes += 1
                summary["writes"] = writes

        self.stdout.write(json.dumps(summary, sort_keys=True))

        if options["strict"] and errors:
            raise CommandError(json.dumps(summary, sort_keys=True))
