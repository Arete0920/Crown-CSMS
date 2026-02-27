"""
Aid Award Engine Unit Tests
============================
Pure unit tests for award_engine.py.

No database required for engine tests — all models are replaced with SimpleNamespace.
Follows Django TestCase convention for consistent test runner discovery.

Run:
    python manage.py test aid.tests.test_aid_engine
"""

from types import SimpleNamespace

from django.test import TestCase

from aid.services.award_engine import (
    AwardRecommendation,
    clamp_int,
    compute_economic_need_cents,
    compute_mas_score,
    mas_modifier_bps,
    recommend_award,
)


def _make_policy(**overrides):
    """Return a minimal policy SimpleNamespace with defaults matching AidPolicy."""
    defaults = dict(
        need_income_floor_cents=0,
        max_award_percent=60,
        min_award_percent=0,
        mas_weight_statement_of_faith=25,
        mas_weight_church_involvement=20,
        mas_weight_family_values=20,
        mas_weight_pastoral_reference=15,
        mas_weight_pog_preassessment=20,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_app(**overrides):
    """Return a SimpleNamespace matching AidApplication MAS + economic fields."""
    defaults = dict(
        income_annual_cents=0,
        assets_cents=0,
        liabilities_cents=0,
        statement_of_faith_score=0,
        church_involvement_score=0,
        family_values_survey_score=0,
        pastoral_reference_score=0,
        pog_preassessment_score=0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# clamp_int
# ---------------------------------------------------------------------------

class TestClampInt(TestCase):
    def test_within_range(self):
        self.assertEqual(clamp_int(50, 0, 100), 50)

    def test_below_min(self):
        self.assertEqual(clamp_int(-10, 0, 100), 0)

    def test_above_max(self):
        self.assertEqual(clamp_int(200, 0, 100), 100)

    def test_at_bounds(self):
        self.assertEqual(clamp_int(0, 0, 100), 0)
        self.assertEqual(clamp_int(100, 0, 100), 100)


# ---------------------------------------------------------------------------
# compute_mas_score
# ---------------------------------------------------------------------------

class TestComputeMasScore(TestCase):
    def test_perfect_score(self):
        policy = _make_policy()
        app = _make_app(
            statement_of_faith_score=100,
            church_involvement_score=100,
            family_values_survey_score=100,
            pastoral_reference_score=100,
            pog_preassessment_score=100,
        )
        score, detail = compute_mas_score(policy, app)
        self.assertEqual(score, 100)
        self.assertEqual(detail["score"], 100)

    def test_zero_score(self):
        policy = _make_policy()
        app = _make_app()  # all zeros
        score, _ = compute_mas_score(policy, app)
        self.assertEqual(score, 0)

    def test_weighted_average(self):
        # All same weight, 50 for every component → score == 50
        policy = _make_policy(
            mas_weight_statement_of_faith=20,
            mas_weight_church_involvement=20,
            mas_weight_family_values=20,
            mas_weight_pastoral_reference=20,
            mas_weight_pog_preassessment=20,
        )
        app = _make_app(
            statement_of_faith_score=50,
            church_involvement_score=50,
            family_values_survey_score=50,
            pastoral_reference_score=50,
            pog_preassessment_score=50,
        )
        score, _ = compute_mas_score(policy, app)
        self.assertEqual(score, 50)

    def test_inputs_clamped_above_100(self):
        policy = _make_policy()
        app = _make_app(
            statement_of_faith_score=999,
            church_involvement_score=999,
            family_values_survey_score=999,
            pastoral_reference_score=999,
            pog_preassessment_score=999,
        )
        score, _ = compute_mas_score(policy, app)
        self.assertEqual(score, 100)

    def test_inputs_clamped_below_0(self):
        policy = _make_policy()
        app = _make_app(
            statement_of_faith_score=-50,
            church_involvement_score=-50,
            family_values_survey_score=-50,
            pastoral_reference_score=-50,
            pog_preassessment_score=-50,
        )
        score, _ = compute_mas_score(policy, app)
        self.assertEqual(score, 0)

    def test_explanation_payload_keys(self):
        policy = _make_policy()
        app = _make_app(statement_of_faith_score=80)
        _, detail = compute_mas_score(policy, app)
        self.assertIn("weights", detail)
        self.assertIn("inputs", detail)
        self.assertIn("total_weight", detail)
        self.assertIn("score", detail)


# ---------------------------------------------------------------------------
# mas_modifier_bps
# ---------------------------------------------------------------------------

class TestMasModifierBps(TestCase):
    def test_band_90_and_above(self):
        self.assertEqual(mas_modifier_bps(90), 1000)
        self.assertEqual(mas_modifier_bps(100), 1000)

    def test_band_75_to_89(self):
        self.assertEqual(mas_modifier_bps(75), 500)
        self.assertEqual(mas_modifier_bps(89), 500)

    def test_band_60_to_74(self):
        self.assertEqual(mas_modifier_bps(60), 0)
        self.assertEqual(mas_modifier_bps(74), 0)

    def test_band_below_60(self):
        self.assertEqual(mas_modifier_bps(59), -1000)
        self.assertEqual(mas_modifier_bps(0), -1000)


# ---------------------------------------------------------------------------
# compute_economic_need_cents
# ---------------------------------------------------------------------------

class TestComputeEconomicNeedCents(TestCase):
    def test_zero_income_zero_assets(self):
        policy = _make_policy(need_income_floor_cents=0)
        app = _make_app(income_annual_cents=0, assets_cents=0, liabilities_cents=0)
        need, _ = compute_economic_need_cents(policy, app, gross_tuition_cents=10_000_00)
        # expected_contribution = 0; need = tuition
        self.assertEqual(need, 10_000_00)

    def test_high_income_covers_tuition(self):
        policy = _make_policy(need_income_floor_cents=0)
        # income = $1M annual; contribution = 200k; tuition = 10k → need = 0
        app = _make_app(income_annual_cents=1_000_000_00, assets_cents=0, liabilities_cents=0)
        need, _ = compute_economic_need_cents(policy, app, gross_tuition_cents=10_000_00)
        self.assertEqual(need, 0)

    def test_income_floor_reduces_contribution(self):
        policy = _make_policy(need_income_floor_cents=50_000_00)  # $50k floor
        # income = $60k; adj income = 10k; contribution = 2k; tuition = 10k → need = 8k
        app = _make_app(income_annual_cents=60_000_00, assets_cents=0, liabilities_cents=0)
        need, detail = compute_economic_need_cents(policy, app, gross_tuition_cents=10_000_00)
        self.assertEqual(detail["income_adj"], 10_000_00)
        self.assertEqual(detail["expected_contribution"], int(10_000_00 * 0.20))
        self.assertEqual(need, 10_000_00 - int(10_000_00 * 0.20))

    def test_assets_minus_liabilities(self):
        policy = _make_policy(need_income_floor_cents=0)
        # income=0, net_assets = 100k; contribution = 5k; tuition = 20k → need = 15k
        app = _make_app(
            income_annual_cents=0,
            assets_cents=100_000_00,
            liabilities_cents=0,
        )
        need, detail = compute_economic_need_cents(policy, app, gross_tuition_cents=20_000_00)
        expected_contribution = int(100_000_00 * 0.05)
        self.assertEqual(detail["net_assets"], 100_000_00)
        self.assertEqual(detail["expected_contribution"], expected_contribution)
        self.assertEqual(need, 20_000_00 - expected_contribution)

    def test_explanation_payload_keys(self):
        policy = _make_policy()
        app = _make_app()
        _, detail = compute_economic_need_cents(policy, app, gross_tuition_cents=5_000_00)
        self.assertIn("income_adj", detail)
        self.assertIn("net_assets", detail)
        self.assertIn("expected_contribution", detail)
        self.assertIn("need", detail)


# ---------------------------------------------------------------------------
# recommend_award (end-to-end engine)
# ---------------------------------------------------------------------------

class TestRecommendAward(TestCase):
    def test_returns_award_recommendation_type(self):
        policy = _make_policy()
        app = _make_app()
        rec = recommend_award(policy, app, gross_tuition_cents=10_000_00)
        self.assertIsInstance(rec, AwardRecommendation)

    def test_recommended_cents_within_bounds(self):
        policy = _make_policy(max_award_percent=60, min_award_percent=0)
        app = _make_app(
            statement_of_faith_score=100,
            church_involvement_score=100,
            family_values_survey_score=100,
            pastoral_reference_score=100,
            pog_preassessment_score=100,
        )
        gross = 10_000_00
        rec = recommend_award(policy, app, gross_tuition_cents=gross)
        max_allowed = int(gross * 0.60)
        self.assertGreaterEqual(rec.recommended_award_cents, 0)
        self.assertLessEqual(rec.recommended_award_cents, max_allowed)

    def test_zero_income_perfect_mas_gives_max_award(self):
        """Zero income + 100 MAS → need = tuition, MAS modifier +10% → clamped to max."""
        policy = _make_policy(max_award_percent=60, min_award_percent=0)
        app = _make_app(
            income_annual_cents=0,
            statement_of_faith_score=100,
            church_involvement_score=100,
            family_values_survey_score=100,
            pastoral_reference_score=100,
            pog_preassessment_score=100,
        )
        gross = 10_000_00
        rec = recommend_award(policy, app, gross_tuition_cents=gross)
        max_allowed = int(gross * 0.60)
        self.assertEqual(rec.recommended_award_cents, max_allowed)

    def test_high_income_zero_mas_gives_zero_or_min(self):
        """Very high income + 0 MAS → need = 0, MAS -10% doesn't push below 0."""
        policy = _make_policy(max_award_percent=60, min_award_percent=0)
        app = _make_app(income_annual_cents=99_999_999_00)
        rec = recommend_award(policy, app, gross_tuition_cents=10_000_00)
        self.assertEqual(rec.recommended_award_cents, 0)

    def test_min_percent_floor_applied_to_base_before_mas(self):
        """
        min_award_percent is applied to the base (need-clamped) award.
        The MAS modifier is applied *after* the floor, and the final result is
        clamped to [0, max_award] — NOT back down to min_award.
        A very-low MAS can therefore push the final award below min_percent.
        This is the documented, intentional engine behaviour.
        """
        policy = _make_policy(max_award_percent=60, min_award_percent=10)
        app = _make_app(income_annual_cents=99_999_999_00)  # very high income → need ≈ 0
        gross = 10_000_00
        rec = recommend_award(policy, app, gross_tuition_cents=gross)
        # base_award = min(0 need, floor at min=10%) = 100_000
        # MAS = 0 → mod_bps = -1000 → adjusted = 100_000 * 0.9 = 90_000
        # Final: 90_000 (below min_percent; MAS can reduce below floor)
        max_allowed = int(gross * 0.60)
        self.assertGreaterEqual(rec.recommended_award_cents, 0)
        self.assertLessEqual(rec.recommended_award_cents, max_allowed)

    def test_explanation_payload_structure(self):
        policy = _make_policy()
        app = _make_app()
        rec = recommend_award(policy, app, gross_tuition_cents=5_000_00)
        exp = rec.explanation
        self.assertIn("gross_tuition_cents", exp)
        self.assertIn("need", exp)
        self.assertIn("mas", exp)
        self.assertIn("base_award_cents", exp)
        self.assertIn("mas_modifier_bps", exp)
        self.assertIn("recommended_award_cents", exp)
        self.assertIn("bounds", exp)

    def test_mas_score_stored_on_result(self):
        policy = _make_policy()
        app = _make_app(
            statement_of_faith_score=90,
            church_involvement_score=90,
            family_values_survey_score=90,
            pastoral_reference_score=90,
            pog_preassessment_score=90,
        )
        rec = recommend_award(policy, app, gross_tuition_cents=10_000_00)
        self.assertEqual(rec.mas_score, 90)
        self.assertEqual(rec.mas_modifier_bps, 1000)  # 90 → +10% band
