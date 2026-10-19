"""Behavioral tests for first-party survey answer validation (not health smoke tests)."""
from types import SimpleNamespace

import pytest

from survey_sentiment.validation import SurveyAnswerValidationError, validate_answers


def q(key, kind, *, choices=None, required=True):
    return SimpleNamespace(key=key, question_type=kind, choices=choices or [], required=required)


QUESTIONS = [
    q("rating", "scale"),
    q("source", "choice", choices=["family", "church", "other"]),
    q("topics", "multi", choices=["teaching", "communication", "support"]),
    q("followup", "boolean"),
    q("comment", "text", required=False),
]


def test_valid_typed_response_round_trip():
    result = validate_answers(QUESTIONS, {
        "rating": 4, "source": "church",
        "topics": ["teaching", "support"], "followup": False,
    })
    assert result == {
        "rating": 4, "source": "church",
        "topics": ["teaching", "support"], "followup": False,
    }


@pytest.mark.parametrize("answers, key", [
    ({}, "rating"),
    ({"rating": False}, "rating"),
    ({"rating": 4.5}, "rating"),
    ({"rating": 6}, "rating"),
    ({"rating": "4"}, "rating"),
    ({"rating": float("nan")}, "rating"),
    ({"rating": float("inf")}, "rating"),
    ({"rating": float("-inf")}, "rating"),
    ({"rating": 10 ** 309}, "rating"),
    ({"rating": -(10 ** 309)}, "rating"),
    ({"rating": 3, "source": "not-an-option"}, "source"),
    ({"rating": 3, "source": "family", "topics": ["teaching", "teaching"]}, "topics"),
    ({"rating": 3, "source": "family", "topics": ["outside"]}, "topics"),
    ({"rating": 3, "source": "family", "topics": "teaching"}, "topics"),
    ({"rating": 3, "source": "family", "topics": ["teaching"], "followup": "false"}, "followup"),
    ({"rating": 3, "source": "family", "topics": ["teaching"], "followup": True, "unrecognized": "secret"}, "unrecognized"),
    ({"rating": 3, "source": "family", "topics": ["teaching"], "followup": True, "comment": "x" * 4001}, "comment"),
])
def test_invalid_question_answer_fails_closed(answers, key):
    with pytest.raises(SurveyAnswerValidationError) as exc:
        validate_answers(QUESTIONS, answers)
    assert key in exc.value.errors


def test_scale_integer_valued_float_remains_accepted():
    assert validate_answers([q("rating", "scale")], {"rating": 5.0}) == {"rating": 5}


def test_invalid_container_is_rejected():
    with pytest.raises(SurveyAnswerValidationError):
        validate_answers(QUESTIONS, ["not", "a", "mapping"])


def test_duplicate_question_keys_are_invalid_instrument():
    with pytest.raises(SurveyAnswerValidationError) as exc:
        validate_answers([q("same", "text"), q("same", "choice")], {})
    assert "instrument" in exc.value.errors


def test_empty_question_set_cannot_accept_responses():
    with pytest.raises(SurveyAnswerValidationError):
        validate_answers([], {})


def test_unknown_question_type_is_denied():
    with pytest.raises(SurveyAnswerValidationError) as exc:
        validate_answers([q("unexpected", "script")], {"unexpected": "payload"})
    assert "unexpected" in exc.value.errors


def test_optional_text_may_be_omitted():
    assert validate_answers([q("memo", "text", required=False)], {}) == {}


@pytest.mark.parametrize("kind,choices,required", [
    ("script", [], False),
    ({"unexpected": "kind"}, [], False),
    (["text"], [], False),
    ("choice", [], False),
    ("choice", ["only"], False),
    ("choice", ["duplicate", "duplicate"], False),
    ("choice", ["valid", 1], False),
    ("choice", [["nested"], ["values"]], False),
    ("choice", {"first": "one", "second": "two"}, False),
    ("choice", "first,second", False),
    ("multi", ["valid", " "], False),
    ("multi", ["valid", "x" * 121], False),
    ("multi", [str(i) for i in range(41)], False),
    ("text", ["unexpected"], False),
    ("boolean", [], "false"),
    ("scale", [], 0),
])
def test_malformed_optional_instrument_is_rejected_even_without_answers(kind, choices, required):
    question = SimpleNamespace(key="optional", question_type=kind, choices=choices, required=required)
    with pytest.raises(SurveyAnswerValidationError) as exc:
        validate_answers([question], {})
    assert "optional" in exc.value.errors


def test_valid_optional_choice_can_be_omitted():
    assert validate_answers([q("optional", "choice", choices=["one", "two"], required=False)], {}) == {}
