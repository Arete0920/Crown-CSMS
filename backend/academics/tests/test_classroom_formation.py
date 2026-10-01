from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.tests.test_classroom_collaboration import create, listing, action, URL
from academics.collaboration_models import ClassroomRecord
from academics.models import TeacherAssignment
from core.models import School, Staff, UserAccount, UserRole
from spiritual_life.formation_models import PortraitDomain, BiblicalWorldviewPriority

pytestmark=pytest.mark.django_db


def test_service_aligns_to_school_domains_without_personal_faith_score(classroom):
    c=classroom
    domain=PortraitDomain.objects.create(school=c[0],name='Serve others')
    priority=BiblicalWorldviewPriority.objects.create(school=c[0],title='Stewardship')
    metadata={'portrait_domain_id':str(domain.id),'worldview_priority_id':str(priority.id),'scripture_reference':'Mark 10:45'}
    assert create(c,kind='service',metadata=metadata).status_code==201
    assert listing(c,3,'student').data['portrait_domains'][0]['name']=='Serve others'
    assert action(c,ClassroomRecord.objects.get(),3,'student',action='respond',student_id=str(c[4].id),content='I helped prepare supplies for our neighbors.').status_code==200
    assert create(c,kind='service',metadata={'faith_score':100}).status_code==400
    foreign=PortraitDomain.objects.create(school=School.objects.create(name='Other school'),name='Foreign')
    assert create(c,kind='service',metadata={'portrait_domain_id':str(foreign.id)}).status_code==404


def test_guardian_family_service_is_for_verified_child(classroom):
    c=classroom
    assert create(c,2,'parent',kind='family_service',student_id=str(c[4].id),visibility='class').status_code==201
    record=ClassroomRecord.objects.get()
    assert record.visibility=='family'
    assert listing(c,3,'student').data['records'][0]['id']==record.id
    assert create(c,2,'parent',kind='family_service').status_code==400
    assert create(c,3,'student',kind='family_service',student_id=str(c[4].id)).status_code==403


def test_coaching_is_private_to_target_teacher_and_leadership(classroom):
    c=classroom
    leader=UserAccount.objects.create_user(username='formation-leader',school=c[0]);UserRole.objects.create(user=leader,school=c[0],role_code='ADMIN')
    extra=c+(leader,)
    assert create(extra,9,'admin',kind='coaching',metadata={'teacher_account_id':str(c[1].id)},due_at=(timezone.now()+timedelta(days=7)).isoformat()).status_code==201
    record=ClassroomRecord.objects.get()
    assert record.owner==c[1]
    data=listing(c,1,'teacher').data['records'][0]
    assert data['can_close'] is False
    assert action(c,record).status_code==200
    record.refresh_from_db()
    assert action(c,record,action='resolve').status_code==403
    assert listing(c,2,'parent').data['records']==[]
    other=UserAccount.objects.create_user(username='co-teacher',email='co-teacher@example.com',school=c[0])
    other.staff=Staff.objects.create(school=c[0],first_name='Other',last_name='Teacher',role_type='TEACHER',status='ACTIVE');other.save()
    UserRole.objects.create(user=other,school=c[0],role_code='TEACHER')
    TeacherAssignment.objects.create(school_id=c[0].id,section=c[5],staff=other.staff)
    client=APIClient();client.force_authenticate(other)
    assert client.get(URL,{'audience':'teacher'},HTTP_X_SCHOOL_ID=str(c[0].id)).data['records']==[]
    assert action(extra,record,9,'admin',action='resolve').status_code==200


def test_resource_reflection_uses_private_student_response(classroom):
    c=classroom
    assert create(c,kind='resource',metadata={'reference':'https://example.com/resource','cost_cents':0}).status_code==201
    assert action(c,ClassroomRecord.objects.get(),3,'student',action='respond',student_id=str(c[4].id),content='The diagram clarified the process.').status_code==200
