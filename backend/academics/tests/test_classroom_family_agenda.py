from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.utils import timezone

from academics.family_digest import weekly_agenda
from academics.family_models import ClassroomDisclosure, ClassroomNotificationPreference
from academics.instruction_models import ClassroomDeadlineAdjustment
from academics.models import Assignment, Enrollment, Section, Submission
from academics.tests.test_classroom_experience import classroom
from academics.tests.test_classroom_family import request
from core.models import School
from households.models import Guardian, Student

pytestmark = pytest.mark.django_db


def sibling(c):
    child = Student.objects.create(school_id=c[0].id, household=c[4].household,
                                   first_name='Sibling', last_name='Two')
    Enrollment.objects.create(school_id=c[0].id, section=c[5], student=child)
    return child


def extension(c, child, days):
    return ClassroomDeadlineAdjustment.objects.create(
        school_id=c[0].id, assignment=c[8], student=child,
        due_date=timezone.localdate() + timedelta(days=days),
        instructions='Complete the observation at home', reason_private='Confidential support reason',
        updated_by=c[1],
    )


def test_shared_assignment_has_separate_children_deadlines_and_receipts(classroom):
    c = classroom; child = sibling(c)
    adjustment = extension(c, child, 2)
    Submission.objects.create(school_id=c[0].id, assignment=c[8], enrollment=c[6],
                              status='submitted', submitted_at=timezone.now(), draft_content='Private draft')
    digest = request(c, method='get').data['digest']
    rows = {row['student_id']: row for row in digest['assignments']}
    assert digest['assignments_total'] == 2
    assert rows[c[4].id]['due_date'] == c[8].due_date
    assert rows[c[4].id]['submission_state'] == 'submitted'
    assert rows[child.id]['due_date'] == adjustment.due_date
    assert rows[child.id]['original_due_date'] == c[8].due_date
    assert rows[child.id]['submission_state'] == 'assigned'
    assert rows[child.id]['makeup_instructions'] == adjustment.instructions
    assert rows[child.id]['course'] == 'Science'
    assert digest['recorded_submissions'] == 1
    assert 'Confidential' not in str(digest) and 'Private draft' not in str(digest)


def test_extension_moves_only_that_child_out_of_this_week(classroom):
    c = classroom; child = sibling(c)
    extension(c, child, 10)
    rows = request(c, method='get').data['digest']['assignments']
    assert [row['student_id'] for row in rows] == [c[4].id]


def test_extension_brings_an_old_assignment_into_this_week(classroom):
    c = classroom; sibling(c)
    c[8].due_date = timezone.localdate() - timedelta(days=7); c[8].save()
    extension(c, c[4], 1)
    rows = request(c, method='get').data['digest']['assignments']
    assert [row['student_id'] for row in rows] == [c[4].id]


def test_restricted_sibling_and_unrelated_student_never_enter_agenda(classroom):
    c = classroom; child = sibling(c)
    ClassroomDisclosure.objects.create(school_id=c[0].id, student=child,
        guardian=Guardian.objects.get(account=c[2]), allowed=False, reason='Verified restriction', updated_by=c[1])
    rows = request(c, method='get').data['digest']['assignments']
    assert [row['student_id'] for row in rows] == [c[4].id]
    assert 'Sibling' not in str(rows)
    other = School.objects.create(name='Other tenant')
    assert request((other, *c[1:]), method='get').status_code == 404


def test_inactive_child_and_unpublished_work_are_excluded(classroom):
    c = classroom; child = sibling(c)
    child.is_active = False; child.save()
    Assignment.objects.create(school_id=c[0].id, section=c[5], category=c[7],
        name='Unpublished work', points_possible=5, due_date=timezone.localdate(), is_published=False)
    rows = request(c, method='get').data['digest']['assignments']
    assert len(rows) == 1 and rows[0]['student_id'] == c[4].id


def test_cap_counts_child_assignment_pairs_and_full_window_receipts(classroom):
    c = classroom; child = sibling(c)
    extra = Assignment.objects.create(school_id=c[0].id, section=c[5], category=c[7],
        name='Later work', points_possible=5, due_date=timezone.localdate() + timedelta(days=1))
    child_enrollment = Enrollment.objects.get(student=child, section=c[5])
    Submission.objects.create(school_id=c[0].id, enrollment=child_enrollment, assignment=extra,
                              status='returned', submitted_at=timezone.now())
    start = timezone.localdate()
    digest = weekly_agenda(c[0].id, Section.objects.filter(id=c[5].id),
        Student.objects.filter(household=c[4].household), start, start + timedelta(days=6), limit=2)
    assert len(digest['assignments']) == 2 and digest['assignments_total'] == 4
    assert digest['truncated'] is True and digest['recorded_submissions'] == 1


def test_agenda_window_uses_guardian_timezone(classroom, monkeypatch):
    c = classroom
    fixed = datetime(2026, 10, 4, 1, 0, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(timezone, 'now', lambda: fixed)
    ClassroomNotificationPreference.objects.create(school_id=c[0].id, account=c[2], timezone='America/New_York')
    c[8].due_date = fixed.date() - timedelta(days=1); c[8].save()
    digest = request(c, method='get').data['digest']
    assert digest['from'] == c[8].due_date
    assert len(digest['assignments']) == 1


def test_empty_week_is_not_a_missing_or_zero_grade(classroom):
    c = classroom; c[8].due_date = None; c[8].save()
    digest = request(c, method='get').data['digest']
    assert digest['assignments'] == [] and digest['assignments_total'] == 0
    assert digest['recorded_submissions'] == 0 and digest['truncated'] is False


def test_corrupt_tenant_links_cannot_change_deadlines_or_expose_receipts(classroom):
    c = classroom; child = sibling(c)
    other = School.objects.create(name='Unrelated school')
    ClassroomDeadlineAdjustment.objects.create(school_id=other.id, assignment=c[8], student=c[4],
        due_date=timezone.localdate() + timedelta(days=3), instructions='Wrong tenant instructions',
        reason_private='Private', updated_by=c[1])
    foreign_enrollment = Enrollment.objects.get(student=child)
    receipt = Submission.objects.create(school_id=c[0].id, enrollment=c[6], assignment=c[8],
                                        status='submitted', submitted_at=timezone.now())
    # Simulate historical corruption below the normal tenant guards; application
    # writes must continue rejecting these relationships.
    from django.db import connection
    for instance in (foreign_enrollment, receipt):
        model = type(instance)
        school_value = model._meta.get_field('school_id').get_db_prep_value(other.id, connection)
        pk_value = model._meta.pk.get_db_prep_value(instance.pk, connection)
        with connection.cursor() as cursor:
            cursor.execute(f'UPDATE {connection.ops.quote_name(model._meta.db_table)} '
                           'SET school_id = %s WHERE id = %s', [school_value, pk_value])
    digest = request(c, method='get').data['digest']
    assert len(digest['assignments']) == 1
    assert digest['assignments'][0]['due_date'] == c[8].due_date
    assert digest['assignments'][0]['makeup_instructions'] == ''
    assert digest['recorded_submissions'] == 0


def test_agenda_query_count_does_not_grow_with_children(classroom, django_assert_num_queries):
    c = classroom; sibling(c)
    start = timezone.localdate()
    with django_assert_num_queries(4):
        digest = weekly_agenda(c[0].id, Section.objects.filter(id=c[5].id),
            Student.objects.filter(household=c[4].household), start, start + timedelta(days=6))
    assert digest['assignments_total'] == 2
