from __future__ import annotations

from collections import Counter, defaultdict

STANDARD_TEMPLATES = {
    "parent_pulse": [
        ("overall_satisfaction", "How satisfied are you with your child's overall experience?", "scale", ["retention", "satisfaction"]),
        ("mission_delivery", "How strongly is the school delivering its Christian mission?", "scale", ["mission", "retention"]),
        ("academic_quality", "How would you rate academic quality?", "scale", ["academics", "retention"]),
        ("communication", "How effective is school communication?", "scale", ["communication", "retention"]),
        ("tuition_pressure", "How much is tuition pressure affecting your family's re-enrollment decision?", "scale", ["affordability", "financial_aid", "retention"]),
        ("reenroll_likelihood", "How likely are you to re-enroll?", "scale", ["retention"]),
        ("improvement", "What is the one thing we could improve?", "text", ["retention"]),
    ],
    "reenrollment_intent": [
        ("intent", "What is your current re-enrollment intention?", "choice", ["retention"]),
        ("primary_factor", "What is the primary factor in that decision?", "choice", ["retention", "affordability", "academics", "mission"]),
        ("aid_needed", "Would additional affordability assistance materially affect your decision?", "boolean", ["financial_aid", "affordability"]),
    ],
    "new_family": [
        ("first_source", "How did you first hear about the school?", "choice", ["marketing", "attribution"]),
        ("decisive_factor", "What most influenced your decision to enroll?", "choice", ["growth", "marketing"]),
        ("other_schools", "What other school options did you seriously consider?", "text", ["competition"]),
        ("affordability", "How significant was affordability in your decision?", "scale", ["affordability", "financial_aid"]),
        ("portrait_priority", "Which student outcomes mattered most to your family?", "multi", ["portrait", "growth"]),
    ],
    "lost_prospect": [
        ("stop_reason", "What most influenced your decision not to continue?", "choice", ["growth", "conversion"]),
        ("affordability", "Was tuition or financial aid a significant factor?", "scale", ["affordability", "financial_aid"]),
        ("experience", "How would you rate your admissions experience?", "scale", ["admissions", "conversion"]),
        ("destination", "What option did you choose instead?", "text", ["competition"]),
    ],
    "exit": [
        ("primary_reason", "What is the primary reason for leaving?", "choice", ["retention"]),
        ("avoidable", "Could the school reasonably have prevented this withdrawal?", "boolean", ["retention"]),
        ("affordability", "Was affordability a significant factor?", "scale", ["affordability", "financial_aid"]),
        ("destination", "Where is the student going next?", "text", ["competition", "retention"]),
        ("recommend", "How likely are you to recommend the school?", "scale", ["sentiment", "retention"]),
    ],
}


def build_template_questions(purpose):
    rows = []
    for order, item in enumerate(STANDARD_TEMPLATES.get(purpose, []), start=1):
        key, prompt, question_type, tags = item
        choices = []
        if key == "intent":
            choices = ["definitely_returning", "probably_returning", "unsure", "probably_leaving", "definitely_leaving"]
        elif key == "primary_factor":
            choices = ["tuition", "financial_aid", "academics", "mission", "leadership", "teachers", "relationships", "athletics", "location", "transportation", "special_needs", "relocation", "other"]
        elif key == "first_source":
            choices = ["parent_referral", "church", "search", "social", "event", "preschool_feeder", "other"]
        elif key in {"decisive_factor", "stop_reason", "primary_reason"}:
            choices = ["christian_mission", "academics", "safety", "community", "teachers", "tuition", "financial_aid", "athletics", "location", "transportation", "student_support", "another_school", "other"]
        rows.append({"key": key, "prompt": prompt, "question_type": question_type, "strategic_tags": tags, "choices": choices, "required": key != "improvement", "sort_order": order})
    return rows


def survey_insights(*, school_id, purpose=None):
    from .models import SurveyAnswer

    answers = SurveyAnswer.objects.filter(response__school_id=school_id)
    if purpose:
        answers = answers.filter(response__survey__purpose=purpose)
    scale_values = defaultdict(list)
    choices = defaultdict(Counter)
    total_responses = answers.values("response_id").distinct().count()
    for row in answers.values("question__key", "question__question_type", "value_json"):
        key = row["question__key"]
        value = row["value_json"] or {}
        raw = value.get("value") if isinstance(value, dict) else value
        if row["question__question_type"] == "scale":
            try:
                scale_values[key].append(float(raw))
            except (TypeError, ValueError):
                pass
        elif row["question__question_type"] in {"choice", "boolean"}:
            choices[key][str(raw)] += 1
    averages = {key: round(sum(vals) / len(vals), 2) for key, vals in scale_values.items() if vals}
    choice_counts = {key: dict(counter) for key, counter in choices.items()}
    retention_attention = False
    if averages.get("reenroll_likelihood") is not None and averages["reenroll_likelihood"] < 3.5:
        retention_attention = True
    if averages.get("tuition_pressure") is not None and averages["tuition_pressure"] >= 3.5:
        retention_attention = True
    return {
        "response_count": total_responses,
        "scale_averages": averages,
        "choice_counts": choice_counts,
        "retention_attention_recommended": retention_attention,
        "guardrail": "Survey results are decision-support evidence and should not be used as deterministic predictions about individual families.",
    }
