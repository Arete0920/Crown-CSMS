"""Governed, aggregate-only survey consumers for CROWN strategic products.

Never returns responses, respondent identities, comments or small cells.
Caller must enforce product entitlement and authorization; no HTTP endpoint
is exposed here.
"""
from .models import SurveyDefinition
from .reporting import summarized_survey

KINGDOM_PATH_PURPOSES = frozenset({
    "inquiry", "post_tour", "new_family", "parent_pulse",
    "reenrollment_intent", "lost_prospect", "exit",
})
COMPASS_PURPOSES = frozenset({"parent_pulse", "custom"})


def strategic_survey_summary(*, school_id, survey_id, consumer):
    """Return a guarded aggregate report with transparent provenance."""
    purposes = {
        "kingdom_path": KINGDOM_PATH_PURPOSES,
        "crown_compass": COMPASS_PURPOSES,
    }.get(consumer)
    if purposes is None:
        raise ValueError("Unsupported survey consumer.")
    survey = SurveyDefinition.objects.filter(pk=survey_id, school_id=school_id).first()
    if survey is None or survey.purpose not in purposes:
        return None
    report = summarized_survey(school_id=school_id, survey_id=survey_id)
    if report is None:
        return None
    return {
        "consumer": consumer,
        "survey_purpose": survey.purpose,
        "source": "survey_intelligence",
        "school_id": str(school_id),
        "report": report,
        "interpretation": "Aggregated respondent feedback; not an institutional performance determination.",
    }
