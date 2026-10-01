import pytest
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.models import Assignment, Grade, Submission
from academics.family_models import ClassroomDisclosure
from core.models import UserAccount
from households.models import Guardian
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db


def get(c, user, path=None):
    client=APIClient();client.force_authenticate(user)
    return client.get(path or f'/api/v1/gradebook/students/{c[4].id}/grades/', HTTP_X_SCHOOL_ID=str(c[0].id))


def test_summary_requires_relationship_and_honors_disclosure(classroom):
    c=classroom
    for user in c[1:4]: assert get(c,user).status_code==200
    stranger=UserAccount.objects.create_user(username='grade-stranger',school=c[0],is_staff=True)
    assert get(c,stranger).status_code==403
    guardian=Guardian.objects.get(account=c[2])
    ClassroomDisclosure.objects.create(school_id=c[0].id, student=c[4], guardian=guardian, allowed=False, reason='School decision', updated_by=c[1])
    assert get(c,c[2]).status_code==403
    assert get(c,c[3]).status_code==200


def test_primary_teacher_gradebook_access_and_staff_flag_rejected(classroom):
    c=classroom
    assert get(c,c[1],'/api/v1/gradebook/sections/').status_code==200
    stranger=UserAccount.objects.create_user(username='staff-only',school=c[0],is_staff=True)
    assert get(c,stranger,'/api/v1/gradebook/sections/').status_code==403


def test_family_summary_hides_drafts_and_withholds_conflicts(classroom):
    c=classroom
    draft=Assignment.objects.create(school_id=c[0].id,section=c[5],category=c[7],name='Private draft',points_possible=10,is_published=False)
    for assignment in [draft,c[8]]:
        GradeEntry.objects.create(school_id=c[0].id, section=c[5], student=c[4], assignment=assignment, assignment_name=assignment.name, points_possible=10, points_earned=0)
    submission=Submission.objects.create(school_id=c[0].id,enrollment=c[6],assignment=c[8])
    Grade.objects.create(school_id=c[0].id,submission=submission,numeric_score=5)
    result=get(c,c[2]).data['courses'][0]
    assert result['assignments_count']==1
    assert result['assignments'][0]['grade_conflict']
    assert result['assignments'][0]['points_earned'] is None
    assert result['overall_percentage'] is None and result['letter_grade'] is None


def test_primary_teacher_grade_writes_keep_action_permission_gate(classroom):
    from core.models import CrownPermission, RolePermission
    c=classroom
    client=APIClient();client.force_authenticate(c[1])
    url=f'/api/v1/gradebook/sections/{c[5].id}/assignments/{c[8].id}/grades/upsert/'
    payload={'grades':[{'student_id':str(c[4].id),'points_earned':0}]}
    assert client.post(url,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==403
    permission,_=CrownPermission.objects.get_or_create(code='gradebook.edit',defaults={'description':'Grade writes'})
    RolePermission.objects.get_or_create(role_code='TEACHER',permission=permission)
    assert client.post(url,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==200
    c[1].staff.status='INACTIVE';c[1].staff.save()
    assert client.post(url,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==404
