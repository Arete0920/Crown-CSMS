from __future__ import annotations

from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from academics.models import Course
from core.models import School
from curricula.governance import clone_version, create_new_draft, transition_version
from curricula.models import CurriculumMap, CurriculumMapVersion, CurriculumMapVersionEvent, Lesson, Unit

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School, email: str):
    return User.objects.create_user(
        username=f"curriculum-governance-{uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def _course(school: School, code: str) -> Course:
    return Course.objects.create(school_id=school.id, code=code, name=f"Course {code}")


def _map_with_draft(school: School, code="ENG-701", actor=None):
    course = _course(school, code)
    curriculum_map = CurriculumMap.objects.create(
        school_id=school.id,
        course=course,
        title=f"Map {code}",
        grade_band="7",
        subject="English",
    )
    version = create_new_draft(curriculum_map=curriculum_map, actor=actor)
    return curriculum_map, version


def _unit_lesson(school: School, curriculum_map: CurriculumMap, version: CurriculumMapVersion):
    unit = Unit.objects.create(
        school_id=school.id,
        curriculum_map=curriculum_map,
        curriculum_version=version,
        sequence=1,
        title="Foundations",
    )
    lesson = Lesson.objects.create(
        school_id=school.id,
        unit=unit,
        sequence=1,
        title="Lesson One",
        objectives="Objective one",
    )
    return unit, lesson


def test_map_rejects_course_from_another_school():
    school_a = _school("Governance A")
    school_b = _school("Governance B")
    foreign_course = _course(school_b, "BAD-1")
    with pytest.raises(ValidationError):
        CurriculumMap.objects.create(
            school_id=school_a.id,
            course=foreign_course,
            title="Cross-tenant map",
        )


def test_direct_version_status_change_is_blocked():
    school = _school("Governance Direct Status")
    curriculum_map, version = _map_with_draft(school)
    version.status = CurriculumMapVersion.Status.REVIEW
    with pytest.raises(ValidationError):
        version.save()
    version.refresh_from_db()
    assert version.status == CurriculumMapVersion.Status.DRAFT
    assert curriculum_map.versions.count() == 1


def test_submitter_cannot_approve_own_version_but_independent_approver_can():
    school = _school("Governance Segregation")
    submitter = _user(school, "submitter@example.org")
    approver = _user(school, "approver@example.org")
    _curriculum_map, version = _map_with_draft(school, actor=submitter)

    version = transition_version(
        version=version,
        target_status=CurriculumMapVersion.Status.REVIEW,
        actor=submitter,
        notes="Ready for review.",
    )
    with pytest.raises(ValidationError):
        transition_version(
            version=version,
            target_status=CurriculumMapVersion.Status.APPROVED,
            actor=submitter,
        )

    version = transition_version(
        version=version,
        target_status=CurriculumMapVersion.Status.APPROVED,
        actor=approver,
    )
    assert version.approved_by_id == approver.id
    assert version.status == CurriculumMapVersion.Status.APPROVED


def test_superuser_submitter_still_cannot_self_approve():
    school = _school("Governance Superuser Segregation")
    submitter = _user(school, "superuser-submitter@example.org")
    submitter.is_superuser = True
    submitter.save(update_fields=["is_superuser"])
    _curriculum_map, version = _map_with_draft(school, actor=submitter)

    version = transition_version(
        version=version,
        target_status=CurriculumMapVersion.Status.REVIEW,
        actor=submitter,
    )
    with pytest.raises(ValidationError):
        transition_version(
            version=version,
            target_status=CurriculumMapVersion.Status.APPROVED,
            actor=submitter,
        )


def test_approved_version_cannot_regress_to_draft():
    school = _school("Governance Approved Immutable")
    submitter = _user(school, "approved-submit@example.org")
    approver = _user(school, "approved-approve@example.org")
    _curriculum_map, version = _map_with_draft(school, actor=submitter)

    version = transition_version(version=version, target_status=CurriculumMapVersion.Status.REVIEW, actor=submitter)
    version = transition_version(version=version, target_status=CurriculumMapVersion.Status.APPROVED, actor=approver)

    with pytest.raises(ValidationError):
        transition_version(version=version, target_status=CurriculumMapVersion.Status.DRAFT, actor=approver)


def test_publishing_freezes_unit_and_lesson_authoring():
    school = _school("Governance Freeze")
    submitter = _user(school, "freeze-submit@example.org")
    approver = _user(school, "freeze-approve@example.org")
    curriculum_map, version = _map_with_draft(school, actor=submitter)
    unit, lesson = _unit_lesson(school, curriculum_map, version)

    version = transition_version(version=version, target_status=CurriculumMapVersion.Status.REVIEW, actor=submitter)
    version = transition_version(version=version, target_status=CurriculumMapVersion.Status.APPROVED, actor=approver)
    version = transition_version(version=version, target_status=CurriculumMapVersion.Status.PUBLISHED, actor=approver)
    assert version.status == CurriculumMapVersion.Status.PUBLISHED

    unit.title = "Changed after publication"
    with pytest.raises(ValidationError):
        unit.save()
    lesson.title = "Changed lesson"
    with pytest.raises(ValidationError):
        lesson.save()
    with pytest.raises(ValidationError):
        lesson.delete()
    with pytest.raises(ValidationError):
        unit.delete()


def test_publishing_new_version_retires_previous_published_version_atomically():
    school = _school("Governance Supersede")
    submitter = _user(school, "supersede-submit@example.org")
    approver = _user(school, "supersede-approve@example.org")
    curriculum_map, first = _map_with_draft(school, actor=submitter)
    _unit_lesson(school, curriculum_map, first)

    first = transition_version(version=first, target_status=CurriculumMapVersion.Status.REVIEW, actor=submitter)
    first = transition_version(version=first, target_status=CurriculumMapVersion.Status.APPROVED, actor=approver)
    first = transition_version(version=first, target_status=CurriculumMapVersion.Status.PUBLISHED, actor=approver)

    second = clone_version(source=first, actor=submitter, change_summary="Second edition")
    second = transition_version(version=second, target_status=CurriculumMapVersion.Status.REVIEW, actor=submitter)
    second = transition_version(version=second, target_status=CurriculumMapVersion.Status.APPROVED, actor=approver)
    second = transition_version(version=second, target_status=CurriculumMapVersion.Status.PUBLISHED, actor=approver)

    first.refresh_from_db()
    assert first.status == CurriculumMapVersion.Status.RETIRED
    assert second.status == CurriculumMapVersion.Status.PUBLISHED
    assert curriculum_map.versions.filter(status=CurriculumMapVersion.Status.PUBLISHED).count() == 1


def test_clone_creates_independent_draft_copy():
    school = _school("Governance Clone")
    curriculum_map, source = _map_with_draft(school)
    source_unit, source_lesson = _unit_lesson(school, curriculum_map, source)

    clone = clone_version(source=source, change_summary="Clone for revision")
    cloned_unit = clone.units.get()
    cloned_lesson = cloned_unit.lessons.get()

    assert clone.id != source.id
    assert clone.version_number == 2
    assert clone.status == CurriculumMapVersion.Status.DRAFT
    assert cloned_unit.id != source_unit.id
    assert cloned_lesson.id != source_lesson.id
    assert cloned_unit.title == source_unit.title
    assert cloned_lesson.title == source_lesson.title

    cloned_lesson.title = "Revised clone lesson"
    cloned_lesson.save()
    source_lesson.refresh_from_db()
    assert source_lesson.title == "Lesson One"


def test_governance_events_are_append_only():
    school = _school("Governance Events")
    curriculum_map, version = _map_with_draft(school)
    event = CurriculumMapVersionEvent.objects.get(version=version)
    event.notes = "Tampered"
    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        event.delete()
    with pytest.raises(ValidationError):
        curriculum_map.versions.update(status=CurriculumMapVersion.Status.REVIEW)


def test_versioned_map_cannot_change_course_or_be_hard_deleted():
    school = _school("Governance Stable Map")
    curriculum_map, _version = _map_with_draft(school)
    other_course = _course(school, "SCI-701")
    curriculum_map.course = other_course
    with pytest.raises(ValidationError):
        curriculum_map.save()
    with pytest.raises(ValidationError):
        curriculum_map.delete()
