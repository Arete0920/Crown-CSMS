from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from academics.models import Enrollment, TeacherAssignment
from core.models import Family, Student as CoreStudent, StudentIdentityLink, UserAccount, Staff, HouseholdFamilyLink
from crown_api.models import Person, Household as LegacyHousehold, HouseholdMember, UserPersonLink
from households.models import Household, Student
from crown_api.views_scheduling import student_schedule
from rest_framework.test import APIRequestFactory, force_authenticate
from . import test_revisions as revision_helpers
from .test_views import BASE, _fixtures, _headers


class PublicationVisibilityTests(TestCase):
    setUp = revision_helpers.RevisionTests.setUp
    row = revision_helpers.RevisionTests.row
    publish = revision_helpers.RevisionTests.publish

    def identities(self):
        family=Family.objects.create(school=self.school,family_name='Synthetic family')
        core=CoreStudent.objects.create(school=self.school,family=family,student_number='ONE',
            first_name='Test',last_name='Student',dob=date(2011,1,1))
        user=UserAccount.objects.create_user(username='student',email='student@example.invalid',school=self.school)
        household=Household.objects.create(school_id=self.school.id,name='Synthetic household')
        student=Student.objects.create(school_id=self.school.id,household=household,account=user,
            first_name='Test',last_name='Student')
        link=StudentIdentityLink.objects.create(school=self.school,core_student=core,
            compatibility_student=student,source='manual',evidence_reference='synthetic-test-fixture')
        Enrollment.objects.create(school_id=self.school.id,student=student,section=self.section)
        return core,user,link

    def read_student(self, user, student):
        request=APIRequestFactory().get('/api/students/schedule/',**self.headers)
        force_authenticate(request,user=user)
        return student_schedule(request,student_id=student.id)

    def test_student_sees_published_then_removed_meeting(self):
        core,user,_=self.identities(); sid,_=self.publish([self.row()])
        client=APIClient();client.force_authenticate(user=user)
        response=client.get(f'{BASE}my-schedule/',**self.headers)
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data[0]['meetings'][0]['block_code'],'P1')
        self.assertEqual(self.read_student(user,core).data[0]['section_id'],str(self.section.id))
        self.client.post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**self.headers)
        self.assertEqual(client.get(f'{BASE}my-schedule/',**self.headers).data,[])

    def test_teacher_sees_only_assigned_section(self):
        staff=Staff.objects.create(school=self.school,first_name='Test',last_name='Teacher',email='teacher@example.invalid',role_type='TEACHER')
        user=UserAccount.objects.create_user(username='teacher',email='teacher@example.invalid',school=self.school,staff=staff)
        TeacherAssignment.objects.create(school_id=self.school.id,section=self.section,staff=staff)
        self.publish([self.row()]);client=APIClient();client.force_authenticate(user=user)
        r=client.get(f'{BASE}my-schedule/',**self.headers)
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual([s['section_id'] for s in r.data],[str(self.section.id)])

    def test_parent_reads_only_linked_child(self):
        core,_,_=self.identities();self.publish([self.row()])
        user=UserAccount.objects.create_user(username='parent',email='parent@example.invalid',school=self.school)
        person=Person.objects.create(first_name='Test',last_name='Parent')
        UserPersonLink.objects.create(user=user,person=person)
        household=LegacyHousehold.objects.create(household_name='Parent household')
        HouseholdMember.objects.create(household=household,person=person,role='GUARDIAN')
        HouseholdFamilyLink.objects.create(school=self.school,household_id=household.id,family=core.family,source='admissions')
        r=self.read_student(user,core)
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(r.data[0]['meetings'][0]['room_code'],self.room.code)
        HouseholdFamilyLink.objects.all().delete()
        self.assertEqual(self.read_student(user,core).status_code,404)

    def test_pending_mapping_does_not_grant_student_access(self):
        core,user,link=self.identities();link.verification_status='pending';link.save()
        self.publish([self.row()])
        self.assertEqual(self.read_student(user,core).status_code,404)

    def test_other_school_staff_cannot_read_student(self):
        core,_,_=self.identities();other,*_=_fixtures()
        user=UserAccount.objects.create_user(username='other',email='other@example.invalid',school=other,is_staff=True)
        request=APIRequestFactory().get('/api/students/schedule/',**_headers(other));force_authenticate(request,user=user)
        self.assertEqual(student_schedule(request,student_id=core.id).status_code,404)

    def test_unlinked_self_service_shows_no_schedule(self):
        user=UserAccount.objects.create_user(username='unlinked',email='unlinked@example.invalid',school=self.school)
        self.publish([self.row()]);client=APIClient();client.force_authenticate(user=user)
        self.assertEqual(client.get(f'{BASE}my-schedule/',**self.headers).data,[])
