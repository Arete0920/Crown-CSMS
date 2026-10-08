from academics.bju_scope_sequence import (
    BJU_2026_SUBJECT_LANES,
    BJU_SCOPE_SEQUENCE_SOURCES,
    bju_objective_ingestion_ready,
    get_bju_scope_sequence_sources,
)


def test_bju_registry_tracks_current_academic_and_worldview_sources():
    pairs = {(source.academic_year, source.scope_kind) for source in BJU_SCOPE_SEQUENCE_SOURCES}
    assert pairs == {
        (2026, "academic"),
        (2027, "academic"),
        (2026, "biblical_worldview"),
        (2027, "biblical_worldview"),
    }


def test_bju_registry_is_rights_safe_and_fails_closed_for_objective_ingestion():
    assert not bju_objective_ingestion_ready()
    for source in BJU_SCOPE_SEQUENCE_SOURCES:
        assert source.mapping_mode == "official_reference_only"
        assert source.objective_ingestion_authorized is False
        assert source.official_url.startswith("https://www.bjupress.com/")


def test_bju_registry_can_filter_by_year_and_kind():
    sources_2027 = get_bju_scope_sequence_sources(academic_year=2027)
    assert len(sources_2027) == 2
    assert {source.scope_kind for source in sources_2027} == {"academic", "biblical_worldview"}

    academic = get_bju_scope_sequence_sources(scope_kind="academic")
    assert {source.academic_year for source in academic} == {2026, 2027}


def test_2026_subject_lane_index_matches_official_scope_sequence_contents():
    assert BJU_2026_SUBJECT_LANES == (
        "Early Childhood",
        "Reading/Literature",
        "Writing & Grammar",
        "Spelling",
        "Handwriting",
        "Vocabulary",
        "Math",
        "Science",
        "Heritage Studies",
        "Bible",
        "Spanish",
    )
