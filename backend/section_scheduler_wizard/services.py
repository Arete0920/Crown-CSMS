"""Validated, reversible changes to canonical meeting placements.

All callers must authorize publication and hold the academic-year row lock.
Placement revisions retain the old row and an explicit before/after receipt.
"""
from uuid import UUID

from academics.models import Enrollment, Section, TeacherAssignment
from bell_schedule_wizard.models import DayTemplate, PeriodBlock
from room_setup_wizard.models import Room
from rest_framework.exceptions import APIException, ValidationError
from .models import SectionPlacement


class StaleSchedule(APIException):
    status_code = 409
    default_detail = "The schedule changed. Reload it before publishing."


def uid(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("A valid record ID is required.")


def snapshot(p):
    return {"placement_id": str(p.id), "section_id": str(p.section_id),
            "day_template_id": str(p.day_template_id), "period_block_id": str(p.period_block_id),
            "room_id": str(p.room_id) if p.room_id else None,
            "expected_updated_at": p.updated_at.isoformat()}


def normalize(rows, session):
    if not isinstance(rows, list) or not rows:
        raise ValidationError("At least one placement change is required.")
    normalized, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValidationError("Each placement change must be an object.")
        action = row.get("action", "upsert")
        if action not in ("upsert", "remove"):
            raise ValidationError("Unknown placement action.")
        old = None
        if row.get("placement_id"):
            old = SectionPlacement.objects.filter(
                id=uid(row["placement_id"]), school_id=session.school_id,
                academic_year_id=session.academic_year_id, is_active=True,
                section__term=session.term_code,
                section__term_ref__academic_year_id=session.academic_year_id,
            ).first()
            if old is None or row.get("expected_updated_at") != old.updated_at.isoformat():
                raise StaleSchedule()
            if old.id in seen:
                raise ValidationError("A meeting may only be changed once per publication.")
            seen.add(old.id)
        if action == "remove":
            if old is None:
                raise ValidationError("Select an existing meeting to remove.")
            item = snapshot(old)
        else:
            section = Section.objects.filter(
                id=uid(row.get("section_id")), school_id=session.school_id,
                term_ref__academic_year_id=session.academic_year_id, term=session.term_code,
            ).first()
            if section is None or (old and section.id != old.section_id):
                raise ValidationError("The section must belong to the selected school, year and term.")
            template = DayTemplate.objects.filter(
                id=uid(row.get("day_template_id")), schedule__school_id=session.school_id,
                schedule__academic_year_id=session.academic_year_id, schedule__is_active=True,
            ).first()
            block = PeriodBlock.objects.filter(id=uid(row.get("period_block_id")), template=template).first() if template else None
            if block is None:
                raise ValidationError("Select a period from the active bell schedule.")
            room_id = uid(row["room_id"]) if row.get("room_id") else None
            if room_id and not Room.objects.filter(id=room_id, school_id=session.school_id, is_active=True).exists():
                raise ValidationError("Select an active room in this school.")
            item = {"section_id": str(section.id), "day_template_id": str(template.id),
                    "period_block_id": str(block.id), "room_id": str(room_id) if room_id else None}
            if old:
                item.update(placement_id=str(old.id), expected_updated_at=old.updated_at.isoformat())
        normalized.append({**item, "action": action})
    return normalized


def validate_candidates(candidates, remaining, school_id):
    """Check occupied students, staff, rooms, and noninstructional blocks."""
    resources = {}
    def members(section):
        if section.id not in resources:
            students = set(Enrollment.objects.filter(
                school_id=school_id, section_id=section.id, student__school_id=school_id,
                student__is_active=True).values_list("student_id", flat=True))
            teachers = set(TeacherAssignment.objects.filter(
                school_id=school_id, section_id=section.id, staff__school_id=school_id
            ).values_list("staff_id", flat=True))
            resources[section.id] = students, teachers
        return resources[section.id]
    accepted = list(remaining)
    for p in candidates:
        if (p.section.school_id != school_id or p.day_template.schedule.school_id != school_id
                or not p.day_template.schedule.is_active
                or (p.room and (p.room.school_id != school_id or not p.room.is_active))):
            raise ValidationError("A selected class, room, or bell schedule is no longer available.")
        if not p.period_block.is_instructional:
            raise ValidationError("Classes cannot be placed in protected noninstructional periods, including chapel or devotions.")
        students, teachers = members(p.section)
        if p.room and len(students) > p.room.capacity:
            raise ValidationError(f"Room {p.room.code} capacity is {p.room.capacity}; this section has {len(students)} students.")
        for other in accepted:
            if p.day_template_id != other.day_template_id:
                continue
            a, b = p.section.term_ref, other.section.term_ref
            if a and b and ((a.end_date and b.start_date and a.end_date < b.start_date) or
                            (b.end_date and a.start_date and b.end_date < a.start_date)):
                continue
            if p.period_block.start_time >= other.period_block.end_time or other.period_block.start_time >= p.period_block.end_time:
                continue
            if p.section_id == other.section_id:
                raise ValidationError("This section already has a meeting during that period.")
            if p.room_id and p.room_id == other.room_id:
                raise ValidationError(f"Room collision: {p.room.code} is already occupied.")
            other_students, other_teachers = members(other.section)
            if teachers & other_teachers:
                raise ValidationError("Teacher collision: an assigned teacher is already teaching during this period.")
            if students & other_students:
                raise ValidationError("Student collision: enrolled students already have a class during this period.")
        accepted.append(p)


def active_placements(session):
    return SectionPlacement.objects.filter(
        school_id=session.school_id, academic_year_id=session.academic_year_id, is_active=True
    ).select_related("section__term_ref", "room", "period_block", "day_template")


def publish(session):
    rows = normalize(session.sections, session)
    ids = [r["placement_id"] for r in rows if r.get("placement_id")]
    remaining = list(active_placements(session).exclude(id__in=ids))
    candidates = []
    for row in rows:
        if row["action"] == "remove":
            continue
        # Old clients may repeat a placement, but may not overwrite its room blindly.
        match = next((p for p in remaining if str(p.section_id) == row["section_id"] and
                      str(p.day_template_id) == row["day_template_id"] and
                      str(p.period_block_id) == row["period_block_id"]), None)
        if match:
            raise StaleSchedule("This meeting already exists. Reload and edit that meeting explicitly.")
        candidates.append(SectionPlacement(
            school_id=session.school_id, academic_year_id=session.academic_year_id,
            section_id=uid(row["section_id"]), day_template_id=uid(row["day_template_id"]),
            period_block_id=uid(row["period_block_id"]), room_id=uid(row["room_id"]) if row["room_id"] else None, is_active=True))
    validate_candidates(candidates, remaining, session.school_id)
    before = []
    for p in active_placements(session).filter(id__in=ids):
        p.is_active = False
        p.save(update_fields=["is_active", "updated_at"])
        before.append(snapshot(p))
    after = []
    for p in candidates:
        p.save()
        after.append(snapshot(p))
    return {"created": len(after), "updated": len(ids), "total": len(rows),
            "replace_semantics": False, "before": before, "after": after}


def undo(session):
    receipt = session.commit_result or {}
    if "before" not in receipt or "after" not in receipt:
        raise ValidationError("This older publication has no reversible receipt.")
    if receipt.get("undone"):
        return receipt
    before, after = [], []
    for key, expected_active, destination in (("before", False, before), ("after", True, after)):
        for row in receipt[key]:
            p = SectionPlacement.objects.filter(id=row["placement_id"], school_id=session.school_id,
                academic_year_id=session.academic_year_id, is_active=expected_active).first()
            if p is None or p.updated_at.isoformat() != row["expected_updated_at"]:
                raise StaleSchedule("This publication was changed later and cannot be undone automatically.")
            destination.append(p)
    remaining = list(active_placements(session).exclude(id__in=[p.id for p in after]))
    # Restoring an older meeting must still meet today's publication rules.
    validate_candidates(before, remaining, session.school_id)
    for p in after:
        p.is_active = False
        p.save(update_fields=["is_active", "updated_at"])
    for p in before:
        p.is_active = True
        p.save(update_fields=["is_active", "updated_at"])
    return {**receipt, "undone": True}
