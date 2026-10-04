"""
Jireh financial-profile modernization tests.
"""

from datetime import date

from django.test import TestCase
from django.utils import timezone

from aid.models import (
    AidApplication,
    AidAuditEvent,
    AidAward,
    AidDocument,
    AidFinancialLineItem,
    AidFinancialProfile,
    AidHouseholdMember,
    AidPolicy,
)
from aid.services.award_engine import recommend_award
from aid.services.profile_service import (
    build_engine_application,
    build_review_signals,
    carry_forward_profile,
)
from core.models import AcademicYear, Family, School, Student


class TestJirehFinancialProfileModernization(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Jireh Test School")
        self.year1 = AcademicYear.objects.create(
            school=self.school,
            name="2026-27",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
        )
        self.year2 = AcademicYear.objects.create(
            school=self.school,
            name="2027-28",
            start_date=date(2027, 8, 1),
            end_date=date(2028, 5, 31),
        )
        self.family = Family.objects.create(school=self.school, family_name="Taylor")
        self.student = Student.objects.create(
            school=self.school,
            family=self.family,
            student_number="JT001",
            first_name="Jordan",
            last_name="Taylor",
            dob=date(2013, 4, 2),
        )

    def _profile(self, *, consent=True):
        profile = AidFinancialProfile.objects.create(
            school=self.school,
            academic_year=self.year1,
            family=self.family,
            consent_to_reuse=consent,
            verification_status=AidFinancialProfile.STATUS_VERIFIED,
            confirmed_at=timezone.now(),
            last_verified_at=timezone.now(),
        )
        AidHouseholdMember.objects.create(
            profile=profile,
            role=AidHouseholdMember.ROLE_ADULT,
            first_name="Alex",
            last_name="Taylor",
            relationship="Parent",
            financially_responsible=True,
        )
        AidFinancialLineItem.objects.create(
            profile=profile,
            category=AidFinancialLineItem.CATEGORY_INCOME,
            subcategory="wages",
            label="Wages",
            annual_amount_cents=80_000_00,
            verified=True,
            source_type=AidFinancialLineItem.SOURCE_DOCUMENT,
            source_reference="tax-return:2025",
        )
        AidFinancialLineItem.objects.create(
            profile=profile,
            category=AidFinancialLineItem.CATEGORY_ASSET,
            subcategory="savings",
            label="Savings",
            annual_amount_cents=10_000_00,
            verified=True,
        )
        AidFinancialLineItem.objects.create(
            profile=profile,
            category=AidFinancialLineItem.CATEGORY_LIABILITY,
            subcategory="consumer_debt",
            label="Consumer debt",
            annual_amount_cents=5_000_00,
            verified=True,
        )
        return profile

    def test_profile_totals_are_structured_and_deterministic(self):
        profile = self._profile()
        self.assertEqual(
            profile.totals(),
            {
                "income_annual_cents": 80_000_00,
                "assets_cents": 10_000_00,
                "liabilities_cents": 5_000_00,
                "expenses_annual_cents": 0,
            },
        )

    def test_carry_forward_preserves_provenance_but_resets_verification(self):
        source = self._profile()
        current = carry_forward_profile(source_profile=source, academic_year=self.year2)

        self.assertEqual(current.carried_forward_from_id, source.id)
        self.assertEqual(current.verification_status, AidFinancialProfile.STATUS_DRAFT)
        self.assertIsNone(current.confirmed_at)
        self.assertIsNone(current.confirmed_by_id)
        self.assertIsNone(current.last_verified_at)
        self.assertEqual(current.household_members.count(), 1)

        item = current.line_items.get(category=AidFinancialLineItem.CATEGORY_INCOME)
        self.assertEqual(item.source_type, AidFinancialLineItem.SOURCE_PRIOR_YEAR)
        self.assertIn(f"profile:{source.id}/line:", item.source_reference)
        self.assertFalse(item.verified)
        self.assertIsNone(item.verified_at)
        self.assertIsNone(item.verified_by_id)

        event = AidAuditEvent.objects.get(
            entity_type=AidAuditEvent.ENTITY_PROFILE,
            entity_id=str(current.id),
            action="PROFILE_CARRIED_FORWARD",
        )
        self.assertEqual(event.school_id, self.school.id)
        event.refresh_from_db()
        self.assertEqual(
            event.details_json,
            {
                "source_profile_id": str(source.id),
                "academic_year_id": str(self.year2.id),
                "line_item_count": 3,
                "household_member_count": 1,
            },
        )

    def test_carry_forward_requires_explicit_reuse_consent(self):
        source = self._profile(consent=False)
        with self.assertRaises(ValueError):
            carry_forward_profile(source_profile=source, academic_year=self.year2)

    def test_engine_uses_canonical_profile_totals(self):
        profile = self._profile()
        app = AidApplication.objects.create(
            school=self.school,
            academic_year=self.year1,
            family=self.family,
            financial_profile=profile,
            income_annual_cents=1,
            assets_cents=2,
            liabilities_cents=3,
        )
        engine_input = build_engine_application(app)
        self.assertEqual(engine_input.income_annual_cents, 80_000_00)
        self.assertEqual(engine_input.assets_cents, 10_000_00)
        self.assertEqual(engine_input.liabilities_cents, 5_000_00)

    def test_review_signals_explain_unverified_and_missing_document_evidence(self):
        source = self._profile()
        current = carry_forward_profile(source_profile=source, academic_year=self.year2)
        app = AidApplication.objects.create(
            school=self.school,
            academic_year=self.year2,
            family=self.family,
            financial_profile=current,
            status=AidApplication.STATUS_SUBMITTED,
        )
        AidDocument.objects.create(
            school=self.school,
            aid_application=app,
            doc_type=AidDocument.DOC_TAX_RETURN,
            received=False,
        )

        signals = build_review_signals(app)
        codes = {signal["code"] for signal in signals}
        self.assertIn("PROFILE_NOT_CONFIRMED", codes)
        self.assertIn("UNVERIFIED_FINANCIAL_ITEMS", codes)
        self.assertIn("MISSING_DOCUMENTS", codes)

    def test_need_award_ignores_mission_modifier_while_mission_award_may_apply_it(self):
        profile = self._profile()
        app = AidApplication.objects.create(
            school=self.school,
            academic_year=self.year1,
            family=self.family,
            financial_profile=profile,
            statement_of_faith_score=100,
            church_involvement_score=100,
            family_values_survey_score=100,
            pastoral_reference_score=100,
            pog_preassessment_score=100,
        )
        policy = AidPolicy.objects.create(
            school=self.school,
            academic_year=self.year1,
            max_award_percent=100,
            min_award_percent=0,
        )
        engine_input = build_engine_application(app)

        need = recommend_award(policy, engine_input, 30_000_00, award_type=AidAward.TYPE_NEED)
        mission = recommend_award(policy, engine_input, 30_000_00, award_type=AidAward.TYPE_MISSION)

        self.assertEqual(need.mas_modifier_bps, 0)
        self.assertEqual(mission.mas_modifier_bps, 1000)
        self.assertEqual(need.economic_need_cents, mission.economic_need_cents)
        self.assertEqual(need.recommended_award_cents, need.economic_need_cents)
        self.assertGreater(mission.recommended_award_cents, need.recommended_award_cents)

        default_need = recommend_award(policy, engine_input, 30_000_00)
        self.assertEqual(default_need, need)
        for field in (
            "statement_of_faith_score", "church_involvement_score",
            "family_values_survey_score", "pastoral_reference_score",
            "pog_preassessment_score",
        ):
            setattr(engine_input, field, 0)
        low_mission_need = recommend_award(policy, engine_input, 30_000_00)
        self.assertEqual(low_mission_need.mas_modifier_bps, 0)
        self.assertEqual(low_mission_need.economic_need_cents, need.economic_need_cents)
        self.assertEqual(low_mission_need.recommended_award_cents, need.recommended_award_cents)

    def test_integer_entity_ids_are_valid_audit_identifiers(self):
        app = AidApplication.objects.create(
            school=self.school,
            academic_year=self.year1,
            family=self.family,
        )
        app.set_status(AidApplication.STATUS_SUBMITTED)
        event = AidAuditEvent.objects.get(
            entity_type=AidAuditEvent.ENTITY_APPLICATION,
            entity_id=str(app.id),
        )
        self.assertEqual(event.action, "STATUS_SUBMITTED")
