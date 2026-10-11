"""Conservative school-scoped survey summary, not a public reporting endpoint.

Do not expose raw answers. Early release disallows segmented filters, mean
ratings, and cross-year comparisons. Until immutable survey publication versions
are present, this only returns provisional distribution counts.
"""
from collections import Counter

from .models import SurveyAnswer, SurveyDefinition, SurveyResponse


MINIMUM_REPORTABLE_RESPONSES = 10
MINIMUM_REPORTABLE_BUCKET = 5


def summarized_survey(*, school_id, survey_id):
    """Return only safe counts for a single school/instrument.

    Suppress an entire question distribution if any nonempty answer bucket is
    smaller than five, preventing deduction from the other buckets/total.
    No caller-supplied subgroup or respondent-level filtering is accepted.
    Access control must be enforced at a separate authenticated boundary.
    """
    survey = SurveyDefinition.objects.filter(school_id=school_id, pk=survey_id).first()
    if survey is None:
        return None

    response_count = SurveyResponse.objects.filter(
        school_id=school_id, survey_id=survey_id,
    ).count()
    report = {
        "survey_id": str(survey.id),
        "status": "provisional_unversioned",
        "minimum_sample": MINIMUM_REPORTABLE_RESPONSES,
        "response_count": response_count if response_count >= MINIMUM_REPORTABLE_RESPONSES else None,
        "suppressed": response_count < MINIMUM_REPORTABLE_RESPONSES,
        "questions": [],
        "limitations": (
            "No causal inference, validated comparisons, respondent-level insight "
            "or cross-year trend is supported by this provisional report."
        ),
    }
    if report["suppressed"]:
        return report

    answers = SurveyAnswer.objects.filter(
        response__school_id=school_id,
        response__survey_id=survey_id,
        question__survey_id=survey_id,
    ).select_related("question")

    grouped = {}
    for answer in answers:
        q = answer.question
        if q.question_type not in {"scale", "choice", "boolean"}:
            continue
        data = answer.value_json
        if not isinstance(data, dict) or "value" not in data:
            continue
        value = data["value"]
        if q.question_type == "scale":
            if type(value) not in (int, float) or value != int(value) or not 1 <= value <= 5:
                continue
            label = str(int(value))
        elif q.question_type == "boolean":
            if type(value) is not bool:
                continue
            label = "yes" if value else "no"
        else:
            if not isinstance(value, str):
                continue
            label = value
        grouped.setdefault(q.key, Counter())[label] += 1

    for question in survey.questions.all():
        counts = grouped.get(question.key)
        if not counts:
            continue
        safe = all(number >= MINIMUM_REPORTABLE_BUCKET for number in counts.values())
        report["questions"].append({
            "question_key": question.key,
            "question_type": question.question_type,
            "suppressed": not safe,
            "distribution": dict(sorted(counts.items())) if safe else None,
            "answered_count": sum(counts.values()) if safe else None,
        })
    return report
