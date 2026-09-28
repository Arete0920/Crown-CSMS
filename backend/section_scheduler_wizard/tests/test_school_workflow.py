"""Synthetic 360-student manual schedule: publish, revise, undo, and teacher read."""
from datetime import time
from django.test import TestCase
from rest_framework.test import APIClient
from academics.models import Course, Section, Enrollment, TeacherAssignment
from bell_schedule_wizard.models import PeriodBlock
from core.models import Staff, UserAccount
from households.models import Household, Student
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import SectionPlacement
from section_scheduler_wizard.services import snapshot
from .test_views import _fixtures, _client_for, _configured_session, _headers, BASE


class SchoolWorkflowTests(TestCase):
    def test_360_student_publication_revision_and_undo(self):
        school, year, initial, day, first_block, first_room = _fixtures()
        client, headers = _client_for(school), _headers(school)
        blocks = [first_block] + [PeriodBlock.objects.create(template=day, code=f'P{n}', label=f'Period {n}',
            start_time=time(7+n), end_time=time(8+n), ordering=n, is_instructional=True) for n in range(2,9)]
        rows=[]
        for grade in range(1,13):
            room=Room.objects.create(school=school,code=f'R{grade}',name=f'Classroom {grade}',capacity=30)
            staff=Staff.objects.create(school=school,first_name='Synthetic',last_name=f'Teacher {grade}',
                email=f'teacher{grade}@example.invalid',role_type='TEACHER')
            household=Household.objects.create(school_id=school.id,name=f'Synthetic cohort {grade}')
            students=[Student.objects.create(school_id=school.id,household=household,first_name=f'Learner {n}',
                last_name=f'Cohort {grade}',grade_level=str(grade)) for n in range(30)]
            for period in range(7):
                course=Course.objects.create(school_id=school.id,code=f'G{grade}S{period}',name=f'Grade {grade} subject {period}')
                section=Section.objects.create(school_id=school.id,course=course,term_ref=initial.term_ref,term='S1',grade_band=str(grade))
                TeacherAssignment.objects.create(school_id=school.id,section=section,staff=staff)
                for student in students:
                    Enrollment.objects.create(school_id=school.id,section=section,student=student)
                rows.append({'section_id':str(section.id),'day_template_id':str(day.id),
                    'period_block_id':str(blocks[period].id),'room_id':str(room.id)})
        sid=_configured_session(client,school,year)
        self.assertEqual(client.post(f'{BASE}{sid}/sections/',{'sections':rows},format='json',**headers).status_code,200)
        r=client.post(f'{BASE}{sid}/commit/',{'confirm':True},format='json',**headers)
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),84)
        self.assertEqual(Student.objects.filter(school_id=school.id).count(),360)
        self.assertEqual(client.get(f'{BASE}{sid}/verify/',**headers).data['count'],84)
        old=SectionPlacement.objects.get(section_id=rows[0]['section_id'],is_active=True)
        edit=_configured_session(client,school,year)
        self.assertEqual(client.post(f'{BASE}{edit}/sections/',{'sections':[{**snapshot(old),
            'period_block_id':str(blocks[7].id)}]},format='json',**headers).status_code,200)
        self.assertEqual(client.post(f'{BASE}{edit}/commit/',{'confirm':True},format='json',**headers).status_code,200)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(),84)
        self.assertEqual(client.post(f'{BASE}{edit}/undo/',{'confirm':True},format='json',**headers).status_code,200)
        old.refresh_from_db();self.assertTrue(old.is_active)
        user=UserAccount.objects.create_user(username='synthetic-teacher',school=school,staff=staff,email='synthetic@example.invalid')
        viewer=APIClient();viewer.force_authenticate(user=user)
        self.assertEqual(len(viewer.get(f'{BASE}my-schedule/',**headers).data),7)
