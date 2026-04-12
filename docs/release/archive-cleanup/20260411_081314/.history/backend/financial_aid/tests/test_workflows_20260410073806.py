import uuid
from decimal import Decimal

from django.test import TestCase

from core.models import School
from financial_aid.models import AidAuditEvent, AidAward, FinancialAidApplication
from financial_aid.workflows import process_financial_aid_application
from onboarding.models_tasks import HelpArticle
from signals.models import BoardExecutiveMetric


class FinancialAidWorkflowTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Workflow Test School")
        self.application = FinancialAidApplication.objects.create(
            school_id=self.school.id,
            household_id=uuid.uuid4(),
            academic_year="2026-2027",
            household_income=Decimal("42000.00"),
            household_size=5,
            status="submitted",
        )

    def test_process_application_creates_review_artifacts(self):
        result = process_financial_aid_application(application_id=self.application.id)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "in_review")
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["need_index"], 0)
        self.assertTrue(AidAward.objects.filter(application=self.application).exists())
        self.assertTrue(
            AidAuditEvent.objects.filter(
                entity_id=self.application.id,
                event_type="APPLICATION_READY_FOR_REVIEW",
            ).exists()
        )
        self.assertEqual(result["solomon_article_slug"], "christian-principles-for-aid-distribution")
        self.assertTrue(
            HelpArticle.objects.filter(slug="christian-principles-for-aid-distribution").exists()
        )
        self.assertTrue(BoardExecutiveMetric.objects.filter(school=self.school).exists())

    def test_process_application_rejects_non_submitted_records(self):
        self.application.status = "decided"
        self.application.save(update_fields=["status"])

        result = process_financial_aid_application(application_id=self.application.id)

        self.assertEqual(result["status"], "error")
        self.assertIn("submitted", result["message"].lower())
