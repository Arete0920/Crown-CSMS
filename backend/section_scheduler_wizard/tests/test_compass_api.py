"""Django integration checks for authorized published Kairos Compass metrics."""
from django.test import TestCase
from section_scheduler_wizard.models import SectionPlacement
from .test_views import BASE, _client_for, _configured_session, _fixtures, _headers

ENDPOINT=BASE+"compass/published/"

class CompassPublishedApiTests(TestCase):
    def setUp(self):
        self.school,self.year,self.section,self.template,self.block,self.room=_fixtures()
        self.client=_client_for(self.school)
    def get(self,client=None,school=None):
        return (client or self.client).get(
            ENDPOINT,{"academic_year_id":str(self.year.id),"term_code":"S1"},
            **_headers(school or self.school))
    def test_empty_authorized_school_is_read_only_and_private(self):
        before=SectionPlacement.objects.count()
        res=self.get()
        self.assertEqual(res.status_code,200,res.data)
        self.assertEqual(res.data["published_meetings"],0)
        self.assertFalse(res.data["publication_allowed"])
        self.assertIsNone(res.data["distinct_students"])
        self.assertIn("no-store",res["Cache-Control"])
        self.assertEqual(SectionPlacement.objects.count(),before)
    def test_missing_school_permission_denied(self):
        from core.models import UserRole
        actor=self.client.handler._force_user
        UserRole.objects.filter(user=actor,school=self.school).delete()
        self.assertEqual(self.get().status_code,403)
    def test_missing_year_or_term_denied(self):
        self.assertEqual(self.client.get(ENDPOINT,{},**_headers(self.school)).status_code,400)
    def test_real_published_card_is_reported_without_student_pii(self):
        sid=_configured_session(self.client,self.school,self.year)
        stage=self.client.post(
            f"{BASE}{sid}/sections/",
            {"sections":[{"section_id":str(self.section.id),"day_template_id":str(self.template.id),
                          "period_block_id":str(self.block.id),"room_id":str(self.room.id)}]},
            format="json",**_headers(self.school))
        self.assertEqual(stage.status_code,200,stage.data)
        publish=self.client.post(f"{BASE}{sid}/commit/",{"confirm":True},format="json",**_headers(self.school))
        self.assertEqual(publish.status_code,200,publish.data)
        res=self.get()
        self.assertEqual(res.status_code,200,res.data)
        self.assertEqual(res.data["published_meetings"],1)
        self.assertTrue(res.data["privacy_suppressed"])
        self.assertIsNone(res.data["meeting_seat_utilization_percent"])
        self.assertNotIn("student_name",str(res.data).lower())
    def test_cross_school_principal_cannot_read(self):
        foreign,*_=_fixtures()
        other=_client_for(foreign)
        res=self.get(client=other)
        self.assertEqual(res.status_code,404)

    def test_concurrent_published_record_change_returns_409(self):
        from unittest.mock import patch
        from section_scheduler_wizard.models import SectionPlacement
        session=_configured_session(self.client,self.school,self.year)
        stage=self.client.post(
            f"{BASE}{session}/sections/",
            {"sections":[{"section_id":str(self.section.id),"day_template_id":str(self.template.id),
                          "period_block_id":str(self.block.id),"room_id":str(self.room.id)}]},
            format="json",**_headers(self.school))
        self.assertEqual(stage.status_code,200,stage.data)
        commit=self.client.post(f"{BASE}{session}/commit/",{"confirm":True},
                                format="json",**_headers(self.school))
        self.assertEqual(commit.status_code,200,commit.data)
        original=SectionPlacement.objects.filter(is_active=True).count()
        self.assertEqual(original,1)
        # After the first read, make the later verification query observe
        # a change. This simulates concurrent publication/undo safely.
        from section_scheduler_wizard import compass_api
        actual=compass_api.summarize_published_kairos
        def side_effect(snapshot, cards):
            SectionPlacement.objects.filter(is_active=True).update(is_active=False)
            return actual(snapshot,cards)
        with patch("section_scheduler_wizard.compass_api.summarize_published_kairos",
                   side_effect=side_effect):
            response=self.get()
        self.assertEqual(response.status_code,409,response.data)
        self.assertEqual(response.data["status"],"PUBLISHED_SCHEDULE_CHANGED")
        self.assertFalse(response.data["publication_allowed"])
