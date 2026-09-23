import datetime

from django.test import TestCase
from rest_framework.test import APIClient
from academics.models import Course, Section, Enrollment, TeacherAssignment
from bell_schedule_wizard.models import PeriodBlock
from core.models import Staff
from households.models import Household, Student
from section_scheduler_wizard.models import SectionPlacement
from section_scheduler_wizard.services import snapshot
from .test_views import _fixtures, _client_for, _configured_session, _headers, BASE


class RevisionTests(TestCase):
    def setUp(self):
        self.school, self.year, self.section, self.day, self.block, self.room = _fixtures()
        self.client = _client_for(self.school)
        self.headers = _headers(self.school)
        self.later = PeriodBlock.objects.create(template=self.day, code='P2', label='Period 2',
            start_time=datetime.time(9), end_time=datetime.time(10), ordering=1, is_instructional=True)

    def row(self, section=None, block=None):
        return {'section_id':str((section or self.section).id), 'day_template_id':str(self.day.id),
                'period_block_id':str((block or self.block).id), 'room_id':str(self.room.id)}

    def publish(self, rows, expected=200):
        sid = _configured_session(self.client, self.school, self.year)
        staged = self.client.post(f'{BASE}{sid}/sections/', {'sections':rows}, format='json', **self.headers)
        self.assertEqual(staged.status_code, 200, staged.data)
        response = self.client.post(f'{BASE}{sid}/commit/', {'confirm':True}, format='json', **self.headers)
        self.assertEqual(response.status_code, expected, response.data)
        return sid, response

    def existing(self):
        self.publish([self.row()])
        return SectionPlacement.objects.get(section=self.section, is_active=True)

    def second_section(self):
        c=Course.objects.create(school_id=self.school.id, code='SECOND', name='Second')
        return Section.objects.create(school_id=self.school.id, course=c, term_ref=self.section.term_ref, term='S1')

    def student(self):
        h=Household.objects.create(school_id=self.school.id, name='Synthetic family')
        return Student.objects.create(school_id=self.school.id, household=h, first_name='Test', last_name='Student')

    def test_move_retains_history_and_undo_restores_original(self):
        old=self.existing()
        sid,_=self.publish([{**snapshot(old),'period_block_id':str(self.later.id)}])
        old.refresh_from_db(); self.assertFalse(old.is_active)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).get().period_block_id,self.later.id)
        r=self.client.post(f'{BASE}{sid}/undo/', {'confirm':True}, format='json', **self.headers)
        self.assertEqual(r.status_code,200,r.data)
        old.refresh_from_db(); self.assertTrue(old.is_active)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),1)

    def test_remove_only_selected_meeting(self):
        old=self.existing()
        self.publish([self.row(block=self.later)])
        self.publish([{**snapshot(old),'action':'remove'}])
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),1)
        self.assertEqual(SectionPlacement.objects.get(is_active=True).period_block_id,self.later.id)

    def test_stale_edit_rejected_with_no_changes(self):
        old=self.existing(); row=snapshot(old)
        old.save(); sid=_configured_session(self.client,self.school,self.year)
        r=self.client.post(f'{BASE}{sid}/sections/',{'sections':[row]},format='json',**self.headers)
        self.assertEqual(r.status_code,409)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),1)

    def test_publish_rechecks_staleness_after_staging(self):
        old=self.existing(); sid=_configured_session(self.client,self.school,self.year)
        r=self.client.post(f'{BASE}{sid}/sections/',{'sections':[{**snapshot(old),'action':'remove'}]},format='json',**self.headers)
        self.assertEqual(r.status_code,200)
        old.save()
        r=self.client.post(f'{BASE}{sid}/commit/',{'confirm':True},format='json',**self.headers)
        self.assertEqual(r.status_code,409)
        self.assertTrue(SectionPlacement.objects.get(id=old.id).is_active)

    def test_undo_rejects_later_edit(self):
        old=self.existing(); sid,_=self.publish([{**snapshot(old),'period_block_id':str(self.later.id)}])
        current=SectionPlacement.objects.get(is_active=True); current.save()
        r=self.client.post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**self.headers)
        self.assertEqual(r.status_code,409)

    def test_protected_chapel_period_rejected(self):
        self.block.is_instructional=False; self.block.save()
        self.publish([self.row()],400)
        self.assertFalse(SectionPlacement.objects.exists())

    def test_capacity_is_enforced(self):
        self.room.capacity=0; self.room.save()
        Enrollment.objects.create(school_id=self.school.id,student=self.student(),section=self.section)
        self.publish([self.row()],400)
        self.assertFalse(SectionPlacement.objects.exists())

    def test_student_conflict_without_room_collision(self):
        second=self.second_section(); student=self.student()
        for section in [self.section,second]:
            Enrollment.objects.create(school_id=self.school.id,student=student,section=section)
        self.publish([{**self.row(),'room_id':None},{**self.row(second),'room_id':None}],400)
        self.assertFalse(SectionPlacement.objects.exists())

    def test_teacher_conflict_without_room_collision(self):
        second=self.second_section()
        staff=Staff.objects.create(school=self.school,first_name='Test',last_name='Teacher',email='test.teacher@example.invalid',role_type='TEACHER')
        for section in [self.section,second]:
            TeacherAssignment.objects.create(school_id=self.school.id,staff=staff,section=section)
        self.publish([{**self.row(),'room_id':None},{**self.row(second),'room_id':None}],400)
        self.assertFalse(SectionPlacement.objects.exists())

    def test_unauthenticated_publication_denied(self):
        sid=_configured_session(self.client,self.school,self.year)
        r=APIClient().post(f'{BASE}{sid}/commit/',{'confirm':True},format='json',**self.headers)
        self.assertIn(r.status_code,(401,403))

    def test_other_school_cannot_undo(self):
        sid,_=self.publish([self.row()]); other_school,*_=_fixtures()
        r=_client_for(other_school).post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**_headers(other_school))
        self.assertEqual(r.status_code,404)

    def test_unprivileged_role_cannot_undo(self):
        sid,_=self.publish([self.row()])
        self.client.handler._force_user.roles.all().delete()
        r=self.client.post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**self.headers)
        self.assertEqual(r.status_code,403)

    def test_repeated_commit_and_undo_are_idempotent(self):
        sid,_=self.publish([self.row()])
        for _ in range(2):
            r=self.client.post(f'{BASE}{sid}/commit/',{'confirm':True},format='json',**self.headers)
            self.assertEqual(r.status_code,200)
        for _ in range(2):
            r=self.client.post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**self.headers)
            self.assertEqual(r.status_code,200)
        self.assertFalse(SectionPlacement.objects.filter(is_active=True).exists())

    def test_existing_room_collision_rejects_new_publication(self):
        self.existing()
        self.publish([self.row(self.second_section())],400)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),1)

    def test_undo_rejects_new_conflict_without_partial_changes(self):
        old=self.existing()
        sid,_=self.publish([{**snapshot(old),'period_block_id':str(self.later.id)}])
        self.publish([self.row(self.second_section())])
        r=self.client.post(f'{BASE}{sid}/undo/',{'confirm':True},format='json',**self.headers)
        self.assertEqual(r.status_code,400)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),2)
        self.assertFalse(SectionPlacement.objects.get(id=old.id).is_active)
