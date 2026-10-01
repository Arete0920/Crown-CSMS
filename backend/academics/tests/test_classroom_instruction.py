import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom, get
from academics.tests.test_submission_workflow import act
from academics.models import Assignment, LessonPlan, Unit, Lesson, PublisherObjective, Grade, Submission
from academics.instruction_models import ClassroomRubric, ClassroomDeadlineAdjustment, ClassroomMasteryEvidence
from academics.lesson_execution_models import LessonPlanLesson
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/instruction/'


def request(c, position=1, audience='teacher', method='post', **data):
    client = APIClient(); client.force_authenticate(c[position])
    if method == 'get': return client.get(URL, {'audience': audience}, HTTP_X_SCHOOL_ID=str(c[0].id))
    return client.post(URL+'?audience='+audience, {'section_id': str(c[5].id), 'request_key': str(uuid.uuid4()), **data}, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def curriculum(c):
    unit = Unit.objects.create(school_id=c[0].id, course=c[5].course, title='Observation unit')
    lesson = Lesson.objects.create(school_id=c[0].id, unit=unit, title='Observe carefully')
    objective = PublisherObjective.objects.create(school_id=c[0].id, lesson=lesson, objective_code='SCI-1', description='Describe observations using evidence')
    plan = LessonPlan.objects.get(section=c[5]); plan.lesson_ids=[str(lesson.id)]; plan.save()
    link=LessonPlanLesson.objects.get(lesson_plan=plan, lesson=lesson); link.planned_minutes=30; link.save()
    return lesson, objective, plan


def test_reusable_rubric_is_immutable_and_cannot_change_after_student_evidence(classroom):
    criteria = [{'name':'Evidence','description':'Describe observations','levels':['Needs evidence','Clear evidence']}]
    assert request(classroom, operation='rubric', title='Observation rubric', criteria=criteria).status_code == 200
    rubric = ClassroomRubric.objects.get()
    args = dict(operation='attach_rubric', assignment_id=str(classroom[8].id), rubric_id=str(rubric.id))
    assert request(classroom, **args).status_code == 200
    assert get(classroom[3], classroom[0], audience='student').data['assignments'][0]['rubric']['criteria'] == criteria
    act(classroom)
    assert request(classroom, **args).status_code == 409
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError): rubric.save()
    with pytest.raises(ValidationError): rubric.delete()


def test_curriculum_alignment_and_plan_reuse_reset_delivery_evidence(classroom):
    lesson, objective, plan = curriculum(classroom)
    assert request(classroom, operation='curriculum', assignment_id=str(classroom[8].id), objective_id=str(objective.id)).status_code == 200
    assignment = Assignment.objects.get(id=classroom[8].id); assert assignment.lesson == lesson
    target = (timezone.localdate()+timedelta(days=1)).isoformat()
    assert request(classroom, operation='copy_plan', plan_id=str(plan.id), plan_date=target).status_code == 200
    copy = LessonPlan.objects.exclude(id=plan.id).get()
    assert copy.teacher_notes_private == ''
    assert copy.lesson_links.get().delivery_status == 'planned'
    assert copy.lesson_links.get().actual_minutes is None
    assert request(classroom, operation='copy_plan', plan_id=str(plan.id), plan_date=target).status_code == 409


def test_makeup_deadline_controls_student_work_and_private_reason_is_withheld(classroom):
    assignment = classroom[8]; assignment.due_date=timezone.localdate()-timedelta(days=5); assignment.save()
    due = timezone.localdate()+timedelta(days=3)
    data = dict(operation='deadline', assignment_id=str(assignment.id), student_id=str(classroom[4].id), version=0,
                due_date=due.isoformat(), instructions='Complete observation and ask for feedback', reason_private='Confidential staff accommodation reason')
    assert request(classroom, **data).status_code == 200
    assert request(classroom, **data).status_code == 409
    workspace = get(classroom[3], classroom[0], audience='student')
    task = workspace.data['assignments'][0]
    assert task['due_date'] == due
    assert task['state'] == 'assigned'
    assert 'Confidential' not in str(workspace.data)
    assert act(classroom, action='submit').data['state'] == 'submitted'
    assert ClassroomDeadlineAdjustment.objects.get().reason_private.startswith('Confidential')


def test_weighted_preview_respects_real_zero_missing_category_and_conflicts(classroom):
    category=classroom[7]; category.weight_percent=100; category.save()
    data = request(classroom, 3, 'student', method='get').data['progress'][0]
    assert data['weighted_preview_percent'] is None
    entry = GradeEntry.objects.create(school_id=classroom[0].id, section=classroom[5], student=classroom[4], assignment=classroom[8], assignment_name='Observation', points_possible=10, points_earned=0)
    data = request(classroom, 3, 'student', method='get').data['progress'][0]
    assert data['weighted_preview_percent'] == 0
    submission=Submission.objects.create(school_id=classroom[0].id, enrollment=classroom[6], assignment=classroom[8], status='graded')
    Grade.objects.create(school_id=classroom[0].id, submission=submission, numeric_score=1)
    data = request(classroom, 3, 'student', method='get').data['progress'][0]
    assert data['weighted_preview_percent'] is None
    assert data['grade_conflicts'] == [str(classroom[8].id)]


def test_mastery_preserves_dated_evidence_instead_of_only_replacing_latest(classroom):
    _, objective, _ = curriculum(classroom)
    request(classroom, operation='curriculum', assignment_id=str(classroom[8].id), objective_id=str(objective.id))
    for level,note in [(1,'Beginning observation'),(3,'Independent explanation supported by evidence')]:
        assert request(classroom, operation='mastery', assignment_id=str(classroom[8].id), student_id=str(classroom[4].id), level=level, note=note).status_code == 200
    assert list(ClassroomMasteryEvidence.objects.values_list('level',flat=True)) == [1,3]
    assert request(classroom, 3, 'student', method='get').data['mastery_history'][1]['note'].startswith('Independent')


def test_accessible_resource_requires_safe_reference_and_alternative_instructions(classroom):
    lesson,_,_=curriculum(classroom)
    args = dict(operation='resource', lesson_id=str(lesson.id), title='Observation guide', url='https://example.com/guide', accessible_description='Text describes the diagram', alternative_instructions='Use the written steps instead of the diagram')
    assert request(classroom, **args).status_code == 200
    args['url']='javascript:alert(1)'; assert request(classroom, **args).status_code == 400
    resource = request(classroom, 3, 'student', method='get').data['resources'][0]
    assert resource['alternative_instructions'].startswith('Use the written')


def test_family_cannot_change_instruction_and_retries_do_not_duplicate_rubrics(classroom):
    data=dict(operation='rubric', title='Evidence rubric', criteria=[{'name':'Evidence','description':'Observed details','levels':['Beginning','Clear']}],request_key=str(uuid.uuid4()))
    assert request(classroom, 2, 'parent', **data).status_code == 403
    assert request(classroom, **data).status_code == 200
    assert request(classroom, **data).status_code == 200
    assert ClassroomRubric.objects.count() == 1


def test_unlinked_teacher_profile_cannot_write_instruction(classroom):
    classroom[1].staff=None; classroom[1].save(update_fields=['staff'])
    assert request(classroom, operation='rubric', title='Blocked', criteria=[]).status_code == 403
