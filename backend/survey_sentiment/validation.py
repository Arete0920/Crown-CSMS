"""First-party, side-effect-free Survey Intelligence answer validation.

This is a reusable internal contract, NOT a public submission endpoint.
It does not establish tenant authorization, respondent anonymity, or publication
immutability; those are separate mandatory release gates.
"""
from math import isfinite


class SurveyAnswerValidationError(ValueError):
    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("Survey answers did not satisfy the instrument contract.")


def validate_answers(questions, submitted):
    """Validate typed answers against this instrument's question objects.

    Unknown keys, duplicate question definitions, invalid choices and malformed
    values fail closed. The caller must first verify the immutable publication
    version, tenant, access rules, consent and survey status.
    """
    if not isinstance(submitted, dict):
        raise SurveyAnswerValidationError({"answers": "Answers must be an object."})

    lookup = {}
    for q in questions:
        key = getattr(q, "key", None)
        if not isinstance(key, str) or not key or key in lookup:
            raise SurveyAnswerValidationError({"instrument": "Question keys must be nonempty and unique."})
        lookup[key] = q

    if not lookup:
        raise SurveyAnswerValidationError({"instrument": "An empty survey cannot accept responses."})
    if len(lookup) > 100:
        raise SurveyAnswerValidationError({"instrument": "Survey exceeds the allowed question count."})

    # Validate every definition before considering missing optional answers.
    # An omitted answer must not make an invalid instrument publishable.
    instrument_errors = {}
    for key, question in lookup.items():
        kind = getattr(question, "question_type", None)
        choices = getattr(question, "choices", [])
        required = getattr(question, "required", False)
        if not isinstance(kind, str) or kind not in {"scale", "choice", "multi", "boolean", "text"}:
            instrument_errors[key] = "Unsupported question type."
        elif type(required) is not bool:
            instrument_errors[key] = "Required must be a boolean."
        elif not isinstance(choices, list):
            instrument_errors[key] = "Choices must be an array."
        elif kind in {"choice", "multi"}:
            if (not 2 <= len(choices) <= 40
                or any(not isinstance(option, str) or not 1 <= len(option.strip()) <= 120 for option in choices)
                or len(set(choices)) != len(choices)):
                instrument_errors[key] = "Provide 2 to 40 distinct text choices."
        elif choices:
            instrument_errors[key] = "Choices are not allowed for this question type."
    if instrument_errors:
        raise SurveyAnswerValidationError(instrument_errors)

    errors = {key: "Unknown question." for key in submitted if key not in lookup}
    normalized = {}

    for key, question in lookup.items():
        kind = getattr(question, "question_type", None)
        choices = getattr(question, "choices", None) or []
        required = bool(getattr(question, "required", False))
        present = key in submitted
        raw = submitted.get(key)
        missing = not present or raw is None or raw == "" or raw == []

        if missing:
            if required:
                errors[key] = "A response is required."
            continue

        if kind == "scale":
            if type(raw) not in (int, float) or not isfinite(raw) or raw != int(raw) or not 1 <= raw <= 5:
                errors[key] = "Select an integer rating from 1 to 5."
            else:
                normalized[key] = int(raw)
        elif kind == "choice":
            if not isinstance(raw, str) or raw not in choices:
                errors[key] = "Choose one available option."
            else:
                normalized[key] = raw
        elif kind == "multi":
            if not isinstance(raw, list) or not raw or any(not isinstance(v, str) or v not in choices for v in raw) or len(raw) != len(set(raw)) or len(raw) > 40:
                errors[key] = "Select distinct available options."
            else:
                normalized[key] = list(raw)
        elif kind == "boolean":
            if type(raw) is not bool:
                errors[key] = "Select yes or no."
            else:
                normalized[key] = raw
        elif kind == "text":
            if not isinstance(raw, str) or not raw.strip() or len(raw) > 4000:
                errors[key] = "Provide text of 1 to 4000 characters."
            else:
                normalized[key] = raw
        else:
            errors[key] = "Unsupported question type."

    if errors:
        raise SurveyAnswerValidationError(errors)
    return normalized
