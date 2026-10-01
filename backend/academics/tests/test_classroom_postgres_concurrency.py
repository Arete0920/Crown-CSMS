"""Real PostgreSQL contention proof; the dedicated CI lane requires this engine."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
import pytest
from django.db import close_old_connections, connection, connections
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.tests.test_classroom_operations import identity
from academics.models import Submission, SubmissionRevision
from academics.family_models import ClassroomConferenceSlot, ClassroomFamilyThread
from academics.operations_models import ClassroomAttendanceAudit
from academics.planning_models import ClassroomPlanningEvent
from core.models import UserAccount, UserRole
from households.models import Guardian

pytestmark=[pytest.mark.django_db(transaction=True), pytest.mark.skipif(connection.vendor!='postgresql', reason='Dedicated PostgreSQL classroom proof lane is required for row-lock evidence.')]


def race(c, requests):
    barrier=Barrier(len(requests))
    def send(item):
        user,url,payload=item
        close_old_connections()
        try:
            client=APIClient();client.force_authenticate(user)
            barrier.wait(timeout=10)
            response=client.post(url,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id))
            return response.status_code,response.data
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        futures=[pool.submit(send,item) for item in requests]
        return [future.result(timeout=30) for future in futures]


@pytest.mark.parametrize('same_retry_key',[False,True])
def test_concurrent_initial_draft_has_one_receipt_and_revision(classroom,same_retry_key):
    c=classroom;key=str(uuid.uuid4())
    url=f'/api/v1/academics/assignments/{c[8].id}/work/?audience=student'
    payload={'student_id':str(c[4].id),'action':'save_draft','content':'Recorded observation','version':0,'request_key':key}
    other={**payload,'request_key':key if same_retry_key else str(uuid.uuid4())}
    results=race(c,[(c[3],url,payload),(c[3],url,other)])
    assert sorted(code for code,_ in results)==([200,200] if same_retry_key else [200,409])
    assert Submission.objects.count()==SubmissionRevision.objects.count()==1
    assert Submission.objects.get().version==1


def test_two_guardians_cannot_book_the_same_conference_slot(classroom):
    c=classroom
    other=UserAccount.objects.create_user(username='concurrent-guardian',email='concurrent-guardian@example.com',school=c[0])
    Guardian.objects.create(school_id=c[0].id,household=c[4].household,account=other,first_name='Other',last_name='Guardian')
    start=timezone.now()+timedelta(days=1)
    slot=ClassroomConferenceSlot.objects.create(school_id=c[0].id,section=c[5],teacher=c[1],starts_at=start,ends_at=start+timedelta(minutes=20),location='Classroom')
    payload={'operation':'book','section_id':str(c[5].id),'student_id':str(c[4].id),'slot_id':str(slot.id),'title':'Learning conference','content':'Discuss next learning steps','request_key':str(uuid.uuid4())}
    url='/api/v1/academics/classroom/family/?audience=parent'
    results=race(c,[(c[2],url,payload),(other,url,{**payload,'request_key':str(uuid.uuid4())})])
    assert sorted(code for code,_ in results)==[200,409]
    assert ClassroomFamilyThread.objects.filter(slot=slot).count()==1
    slot.refresh_from_db();assert slot.state=='booked'


def test_concurrent_roll_call_preserves_one_version_and_audit(classroom):
    c=classroom;identity(c)
    payload={'operation':'attendance','section_id':str(c[5].id),'date':timezone.localdate().isoformat(),'version':0,'items':[{'student_id':str(c[4].id),'status':'PRESENT'}],'reason':'Confirmed roll call','request_key':str(uuid.uuid4())}
    url='/api/v1/academics/classroom/operations/'
    results=race(c,[(c[1],url,payload),(c[1],url,{**payload,'request_key':str(uuid.uuid4())})])
    assert sorted(code for code,_ in results)==[200,409]
    assert ClassroomAttendanceAudit.objects.count()==1


def test_concurrent_capacity_edits_reject_stale_version(classroom):
    c=classroom
    leader=UserAccount.objects.create_user(username='concurrent-leader',email='concurrent-leader@example.com',school=c[0])
    UserRole.objects.create(user=leader,school=c[0],role_code='ADMIN')
    payload={'section_id':str(c[5].id),'target_size':24,'planning_note':'Room planning','version':0,'request_key':str(uuid.uuid4())}
    url='/api/v1/academics/classroom/planning/'
    results=race(c,[(leader,url,payload),(leader,url,{**payload,'target_size':25,'request_key':str(uuid.uuid4())})])
    assert sorted(code for code,_ in results)==[200,409]
    assert ClassroomPlanningEvent.objects.count()==1
