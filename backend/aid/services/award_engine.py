"""
Aid Award Engine
================
Pure, side-effect-free financial aid recommendation computation.

All inputs are duck-typed, enabling unit testing with SimpleNamespace without a
database.  The engine never touches the database; callers persist results.

Field name alignment with real models:
  app.income_annual_cents      = AidApplication.income_annual_cents
  app.assets_cents             = AidApplication.assets_cents        (Phase 7.5+)
  app.liabilities_cents        = AidApplication.liabilities_cents   (Phase 7.5+)
  app.statement_of_faith_score = AidApplication.statement_of_faith_score
  app.church_involvement_score = AidApplication.church_involvement_score
  app.family_values_survey_score = AidApplication.family_values_survey_score
  app.pastoral_reference_score = AidApplication.pastoral_reference_score
  app.pog_preassessment_score  = AidApplication.pog_preassessment_score
  policy.*                     = AidPolicy.*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# MAS computation
# ---------------------------------------------------------------------------

def compute_mas_score(policy, app) -> Tuple[int, Dict[str, Any]]:
    """
    Weighted average MAS score (0-100).

    Weights come from policy; if all weights are zero the score is 0.
    Uses normalisation so weights don't need to sum to any specific value.
    """
    weights: Dict[str, int] = {
        "statement_of_faith": policy.mas_weight_statement_of_faith,
        "church_involvement": policy.mas_weight_church_involvement,
        "family_values": policy.mas_weight_family_values,
        "pastoral_reference": policy.mas_weight_pastoral_reference,
        "pog_preassessment": policy.mas_weight_pog_preassessment,
    }
    total_w = sum(weights.values()) or 1

    raw: Dict[str, int] = {
        "statement_of_faith": clamp_int(app.statement_of_faith_score, 0, 100),
        "church_involvement": clamp_int(app.church_involvement_score, 0, 100),
        "family_values": clamp_int(app.family_values_survey_score, 0, 100),
        "pastoral_reference": clamp_int(app.pastoral_reference_score, 0, 100),
        "pog_preassessment": clamp_int(app.pog_preassessment_score, 0, 100),
    }

    score = int(round(sum(raw[k] * weights[k] for k in raw) / total_w))
    return score, {
        "weights": weights,
        "inputs": raw,
        "total_weight": total_w,
        "score": score,
    }


def mas_modifier_bps(mas_score: int) -> int:
    """
    Crown MAS band → basis-point modifier applied to base award.

      >= 90 → +1000 bps (+10%)
      >= 75 → +500  bps (+5%)
      >= 60 → 0     bps (neutral)
      < 60  → -1000 bps (-10%)
    """
    if mas_score >= 90:
        return 1000
    if mas_score >= 75:
        return 500
    if mas_score >= 60:
        return 0
    return -1000


# ---------------------------------------------------------------------------
# Economic need computation
# ---------------------------------------------------------------------------

def compute_economic_need_cents(policy, app, gross_tuition_cents: int) -> Tuple[int, Dict[str, Any]]:
    """
    Minimal guardrail need formula:

      expected_contribution = max(income - floor, 0) * 0.20
                            + max(assets - liabilities, 0) * 0.05
      need = max(gross_tuition - expected_contribution, 0)
    """
    income_adj = max(app.income_annual_cents - policy.need_income_floor_cents, 0)
    net_assets = max(app.assets_cents - app.liabilities_cents, 0)
    expected_contribution = int(income_adj * 0.20 + net_assets * 0.05)
    need = max(gross_tuition_cents - expected_contribution, 0)
    return need, {
        "income_adj": income_adj,
        "net_assets": net_assets,
        "expected_contribution": expected_contribution,
        "need": need,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AwardRecommendation:
    mas_score: int
    mas_modifier_bps: int
    economic_need_cents: int
    recommended_award_cents: int
    explanation: Dict[str, Any]


def recommend_award(policy, app, gross_tuition_cents: int, award_type: str = "NEED") -> AwardRecommendation:
    """
    Compute a deterministic, explainable award recommendation.

    Economic need is calculated independently from mission-alignment inputs.
    Mission-alignment modifiers are applied only to MISSION awards.

    Returns AwardRecommendation with all intermediate values in .explanation
    for use in transparency screens and audit logs.

    No side effects; does not write to the database.
    """
    mas_score, mas_detail = compute_mas_score(policy, app)
    mission_modifier_candidate_bps = mas_modifier_bps(mas_score)
    mod_bps = mission_modifier_candidate_bps if award_type == "MISSION" else 0

    need_cents, need_detail = compute_economic_need_cents(policy, app, gross_tuition_cents)

    max_award = int(gross_tuition_cents * (policy.max_award_percent / 100.0))
    min_award = int(gross_tuition_cents * (policy.min_award_percent / 100.0))
    base_award = clamp_int(need_cents, min_award, max_award)

    adjusted = int(base_award * (1.0 + mod_bps / 10_000.0))
    adjusted = clamp_int(adjusted, 0, max_award)

    explanation = {
        "gross_tuition_cents": gross_tuition_cents,
        "need": need_detail,
        "mas": mas_detail,
        "base_award_cents": base_award,
        "mas_modifier_bps": mod_bps,
        "mission_modifier_candidate_bps": mission_modifier_candidate_bps,
        "institutional_adjustment": {
            "award_type": award_type,
            "mission_modifier_applied": award_type == "MISSION",
            "applied_modifier_bps": mod_bps,
        },
        "recommended_award_cents": adjusted,
        "bounds": {
            "min_award_cents": min_award,
            "max_award_cents": max_award,
        },
    }

    return AwardRecommendation(
        mas_score=mas_score,
        mas_modifier_bps=mod_bps,
        economic_need_cents=need_cents,
        recommended_award_cents=adjusted,
        explanation=explanation,
    )
