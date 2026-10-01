import uuid
import pytest
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError
from academics.models import Submission, SubmissionRevision
from academics.tests.test_classroom_experience import classroom

pytestmark = pytest.mark.django_db


def act(classroom, position=3, audience='student', **payload):
    school, _, _, _, student, _, _, _, assignment = classroom
    client = APIClient()
    client.force_authenticate(classroom[position])
    data = {'student_id': str(student.id), 'action': 'save_draft', 'content': 'My observations',
            'version': 0, 'request_key': str(uuid.uuid4()), **payload}
    return client.post(f'/api/v1/academics/assignments/{assignment.id}/work/?audience={audience}', data,
                        format='json', HTTP_X_SCHOOL_ID=str(school.id))


def test_draft_submit_retry_feedback_and_revision_preserve_history(classroom):
    saved = act(classroom)
    assert saved.status_code == 200
    assert saved.data['state'] == 'draft'
    key = str(uuid.uuid4())
    submitted = act(classroom, action='submit', version=1, request_key=key)
    assert submitted.data['submitted_at']
    assert act(classroom, action='submit', version=1, request_key=key).status_code == 200
    assert SubmissionRevision.objects.count() == 2
    assert act(classroom, version=2).status_code == 409
    returned = act(classroom, position=1, audience='teacher', action='return', version=2, feedback='Explain your evidence')
    assert returned.data['state'] == 'returned'
    revised = act(classroom, action='submit', version=3, content='Improved observation')
    assert revised.status_code == 200
    assert SubmissionRevision.objects.filter(action='submit').count() == 2
    assert SubmissionRevision.objects.filter(sequence=2).get().content == 'My observations'


def test_parents_cannot_submit_students_work(classroom):
    assert act(classroom, position=2, audience='parent').status_code == 403
    assert not Submission.objects.exists()


def test_students_cannot_return_or_grade_own_work(classroom):
    assert act(classroom, action='return', feedback='Approve').status_code == 403
    assert not Submission.objects.exists()


def test_stale_version_and_conflicting_retry_do_not_overwrite(classroom):
    key = str(uuid.uuid4())
    assert act(classroom, request_key=key).status_code == 200
    assert act(classroom, version=0, content='New text').status_code == 409
    assert act(classroom, request_key=key, content='Different text').status_code == 409
    assert Submission.objects.get().draft_content == 'My observations'


def test_parent_draft_content_is_private(classroom):
    act(classroom)
    school, _, parent, _, student, *_, assignment = classroom
    client = APIClient(); client.force_authenticate(parent)
    response = client.get(f'/api/v1/academics/assignments/{assignment.id}/work/',
                          {'audience': 'parent', 'student_id': str(student.id)}, HTTP_X_SCHOOL_ID=str(school.id))
    assert response.data['content'] == ''
    assert response.data['revisions'] == []


def test_revision_evidence_cannot_be_rewritten_or_deleted(classroom):
    act(classroom)
    revision = SubmissionRevision.objects.get()
    revision.content = 'Rewrite'
    with pytest.raises(ValidationError): revision.save()
    with pytest.raises(ValidationError): revision.delete()
    with pytest.raises(ValidationError): SubmissionRevision.objects.all().update(content='Rewrite')


@pytest.mark.parametrize('extra', [{'action': 'submit', 'content': ''}, {'version': True}, {'request_key': 'bad'}, {'student_id': 'bad'}, {'content': []}])
def test_invalid_actions_do_not_mutate_work(classroom, extra):
    assert act(classroom, **extra).status_code == 400
    assert not Submission.objects.exists()


def test_legacy_submission_api_cannot_bypass_ownership_or_revision_history(classroom):
    act(classroom)
    school, _, parent, *_ = classroom
    submission = Submission.objects.get()
    client = APIClient(); client.force_authenticate(parent)
    url = f'/api/v1/academics/submissions/{submission.id}/'
    assert client.patch(url, {'status': 'graded'}, format='json', HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403
    assert client.delete(url, HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403
    assert submission.revisions.count() == 1


def test_assignment_details_and_publication_validation(classroom):
    school, teacher, *_, category, assignment = classroom
    client = APIClient(); client.force_authenticate(teacher)
    url = f'/api/v1/academics/assignments/{assignment.id}/'
    response = client.patch(url, {'instructions': 'Observe and describe', 'success_criteria': 'Evidence and explanation',
                                 'home_support': 'Ask what changed', 'is_published': False}, format='json', HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    assert response.data['instructions'] == 'Observe and describe'
    assert response.data['is_published'] is False
    assert client.patch(url, {'is_published': 'false'}, format='json', HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400


def test_assignment_copy_is_atomic_draft_and_has_no_student_evidence(classroom):
    from academics.models import Assignment, AssignmentCategory, Section
    school, teacher, *_, section, enrollment, category, assignment = classroom
    other = Section.objects.create(school_id=school.id, course=section.course, teacher=teacher, term=section.term)
    other_category = AssignmentCategory.objects.create(school_id=school.id, section=other, name='Practice')
    assignment.instructions = 'Describe the evidence'; assignment.save()
    client = APIClient(); client.force_authenticate(teacher)
    url = f'/api/v1/academics/assignments/{assignment.id}/copy/'
    targets = [{'section_id': str(other.id), 'category_id': str(other_category.id)}]
    response = client.post(url, {'targets': targets}, format='json', HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 201
    copy = Assignment.objects.get(section=other)
    assert copy.instructions == assignment.instructions
    assert not copy.is_published
    assert not copy.submissions.exists()
    assert client.post(url, {'targets': targets}, format='json', HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    assert Assignment.objects.filter(section=other).count() == 1


def test_disagreeing_grade_sources_require_review_instead_of_silent_fallback(classroom):
    from academics.models import Grade
    from gradebook.models import GradeEntry
    from academics.tests.test_classroom_experience import get
    school, teacher, parent, _, student, section, enrollment, _, assignment = classroom
    submission = Submission.objects.create(school_id=school.id, enrollment=enrollment, assignment=assignment, status='graded')
    Grade.objects.create(school_id=school.id, submission=submission, numeric_score=8)
    GradeEntry.objects.create(school_id=school.id, section=section, student=student, assignment=assignment,
                               assignment_name=assignment.name, points_earned=7, points_possible=10)
    row = get(parent, school, audience='parent').data['assignments'][0]
    assert row['state'] == 'grade_conflict'
    assert row['points_earned'] is None


def test_teacher_feedback_response_does_not_reveal_revised_private_draft(classroom):
    act(classroom, action='submit')
    act(classroom, position=1, audience='teacher', action='return', version=1, feedback='Explain the evidence')
    act(classroom, version=2, content='Private revised draft')
    key = str(uuid.uuid4())
    response = act(classroom, position=1, audience='teacher', action='feedback', version=3,
                   feedback='Review the last submission', request_key=key)
    assert response.status_code == 200
    assert response.data['content'] == ''
    assert all(r['action'] != 'save_draft' for r in response.data['revisions'])
    replay = act(classroom, position=1, audience='teacher', action='feedback', version=3,
                 feedback='Review the last submission', request_key=key)
    assert replay.data == response.data
