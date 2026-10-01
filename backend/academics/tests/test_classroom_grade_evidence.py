import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from academics.tests.test_classroom_experience import classroom, get
from academics.models import Submission
from academics.classroom_progress import progress_rows
from academics.experience_access import classroom_scope
from gradebook.models import GradeEntry

pytestmark=pytest.mark.django_db


def test_single_grade_store_stale_denominator_is_withheld_in_all_readers(classroom):
    c=classroom
    GradeEntry.objects.create(school_id=c[0].id,section=c[5],student=c[4],assignment=c[8],assignment_name=c[8].name,points_earned=5,points_possible=5)
    workspace=get(c[2],c[0],audience='parent').data['assignments'][0]
    assert workspace['state']=='grade_conflict' and workspace['points_earned'] is None
    assert workspace['points_possible']==10
    c[7].weight_percent=100;c[7].save()
    sections,students=classroom_scope(c[2],c[0].id,'parent')
    progress=progress_rows(c[0].id,sections,students)[0]
    assert progress['weighted_preview_percent'] is None and progress['grade_conflicts']==[str(c[8].id)]
    client=APIClient();client.force_authenticate(c[2])
    result=client.get(f'/api/v1/gradebook/students/{c[4].id}/grades/',HTTP_X_SCHOOL_ID=str(c[0].id)).data['courses'][0]
    assert result['overall_percentage'] is None and result['assignments'][0]['grade_conflict']
    assert result['assignments'][0]['source']=='conflict_requires_teacher_review'


def test_possible_points_cannot_change_after_shared_student_evidence(classroom):
    c=classroom
    Submission.objects.create(school_id=c[0].id,enrollment=c[6],assignment=c[8],submitted_at=timezone.now(),status='submitted')
    client=APIClient();client.force_authenticate(c[1])
    url=f'/api/v1/academics/assignments/{c[8].id}/'
    assert client.patch(url,{'points_possible':20},format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==409
    c[8].refresh_from_db();assert c[8].points_possible==10
    assert client.patch(url,{'points_possible':10,'instructions':'Clarified directions'},format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==200
