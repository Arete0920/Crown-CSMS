from datetime import date
import pytest
from academics.praeceptum_lesson_planner import draft_weekly_lessons


def test_weekly_drafts_are_editable_scaffolds_not_publisher_content():
    drafts = draft_weekly_lessons(
        course="Science 5", unit="Unit A",
        lesson_titles=["Lesson 1", "Lesson 2"],
        objectives_by_lesson={"Lesson 1": ["school-objective-1"]},
        start_date=date(2027, 1, 4),
        source_reference="https://publisher.example/reference",
    )
    assert [x.day for x in drafts] == ["2027-01-04", "2027-01-05"]
    assert drafts[0].objectives == ("school-objective-1",)
    assert drafts[1].objectives == ()
    assert drafts[0].direct_instruction == ""
    assert drafts[0].biblical_worldview == ""
    assert drafts[0].to_dict()["planned_minutes"] == 45


@pytest.mark.parametrize("titles,minutes", [
    (["Lesson 1", "Lesson 1"], 45),
    ([""], 45),
    (["Lesson 1"], 0),
    (["Lesson 1"], 481),
    ([str(i) for i in range(8)], 45),
])
def test_invalid_planning_requests_rejected(titles, minutes):
    with pytest.raises(ValueError):
        draft_weekly_lessons(
            course="Math", unit="Unit 1", lesson_titles=titles,
            objectives_by_lesson={}, start_date=date(2027, 1, 4),
            planned_minutes=minutes,
        )
