import pytest

from academics.models import TranscriptEntry
from academics.tests.test_transcript_ro_api import _base_school, _registrar_client, _section

pytestmark = pytest.mark.django_db


def _snapshot(*, letter, gpa_points):
    school, year, student = _base_school()
    term, course, _ = _section(
        school=school, year=year, student=student, code=f"EDGE-{letter}-{gpa_points}",
        term_code="FALL", term_name="Fall", ordering=1,
    )
    TranscriptEntry.objects.create(
        school_id=school.id, student=student, course=course, term=term,
        credit_value="1.00", final_letter_grade=letter, gpa_points=gpa_points,
    )
    response = _registrar_client(school).get(
        f"/api/v1/academics/transcript/{student.id}/", HTTP_X_SCHOOL_ID=str(school.id)
    )
    assert response.status_code == 200, response.content
    return response.json()


@pytest.mark.parametrize(
    "letter,stored,points,attempted,earned,cumulative",
    [
        ("A", "0.00", "4.00", "1.00", "1.00", "4.00"),
        ("A", "4.50", "4.50", "1.00", "1.00", "4.50"),
        ("P", "0.00", None, "1.00", "1.00", None),
        ("I", "0.00", None, "0.00", "0.00", None),
        ("W", "0.00", None, "0.00", "0.00", None),
    ],
)
def test_final_mark_credit_and_gpa_policy(letter, stored, points, attempted, earned, cumulative):
    data = _snapshot(letter=letter, gpa_points=stored)
    row = data["terms"][0]["courses"][0]
    assert row["gpa_points"] == points
    assert row["attempted_credits"] == attempted
    assert row["earned_credits"] == earned
    assert row["gpa_included"] is (letter in {"A", "B", "C", "D", "F"})
    assert data["cumulative_gpa"] == cumulative
