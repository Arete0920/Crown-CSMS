from academics.praeceptum_progress import (
    calculate_curriculum_progress,
)


def test_praeceptum_progress_tracks_five_distinct_curriculum_states():
    progress = calculate_curriculum_progress(
        intended=["A", "B", "C", "D"],
        planned=["A", "B", "C"],
        delivered=["A", "B"],
        assessed=["A"],
        mastered=["A"],
    )

    assert progress.as_dict() == {
        "counts": {
            "intended": 4,
            "planned": 3,
            "delivered": 2,
            "assessed": 1,
            "mastered": 1,
        },
        "coverage_percent": {
            "planned": 75.0,
            "delivered": 50.0,
            "assessed": 25.0,
            "mastered": 25.0,
        },
        "gaps": {
            "intended_not_planned": ["D"],
            "planned_not_delivered": ["C"],
            "delivered_not_assessed": ["B"],
            "assessed_not_mastered": [],
        },
    }


def test_praeceptum_progress_does_not_inflate_coverage_with_out_of_scope_ids():
    progress = calculate_curriculum_progress(
        intended=["A", "B"],
        planned=["A", "OUTSIDE"],
        delivered=["A", "OUTSIDE"],
        assessed=["OUTSIDE"],
        mastered=["OUTSIDE"],
    )

    assert progress.planning_coverage_percent == 50.0
    assert progress.delivery_coverage_percent == 50.0
    assert progress.assessment_coverage_percent == 0.0
    assert progress.mastery_coverage_percent == 0.0


def test_praeceptum_progress_handles_empty_intended_curriculum():
    progress = calculate_curriculum_progress(
        intended=[],
        planned=[],
        delivered=[],
        assessed=[],
        mastered=[],
    )

    assert progress.as_dict()["coverage_percent"] == {
        "planned": 0.0,
        "delivered": 0.0,
        "assessed": 0.0,
        "mastered": 0.0,
    }


def test_praeceptum_gap_sets_preserve_state_boundaries():
    progress = calculate_curriculum_progress(
        intended=["A", "B", "C", "D"],
        planned=["A", "B", "C", "D"],
        delivered=["A", "B", "C"],
        assessed=["A", "B"],
        mastered=["A"],
    )

    assert progress.intended_not_planned == frozenset()
    assert progress.planned_not_delivered == frozenset({"D"})
    assert progress.delivered_not_assessed == frozenset({"C"})
    assert progress.assessed_not_mastered == frozenset({"B"})
