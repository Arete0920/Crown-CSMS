from academics.curriculum_reference_registry import (
    CURRICULUM_REFERENCE_SOURCES,
    get_curriculum_reference_sources,
    structured_publisher_ingestion_ready,
    supported_reference_publishers,
)


def test_registry_includes_priority_christian_curriculum_publishers():
    assert set(supported_reference_publishers()) >= {
        "BJU Press",
        "Abeka",
        "Purposeful Design",
        "Positive Action for Christ",
        "Summit Ministries",
    }


def test_registry_is_public_reference_only_and_fails_closed():
    for source in CURRICULUM_REFERENCE_SOURCES:
        assert source.rights_mode == "public_reference_only"
        assert source.objective_ingestion_authorized is False
        assert source.lesson_content_ingestion_authorized is False
        assert source.official_url.startswith("https://")

    for publisher in supported_reference_publishers():
        assert structured_publisher_ingestion_ready(publisher) is False


def test_registry_filters_by_publisher_alias():
    abeka = get_curriculum_reference_sources(publisher="A Beka")
    assert abeka
    assert {source.publisher for source in abeka} == {"Abeka"}

    purposeful = get_curriculum_reference_sources(publisher="purposeful design")
    assert purposeful
    assert {source.publisher for source in purposeful} == {"Purposeful Design"}


def test_unknown_publisher_returns_no_reference_sources():
    assert get_curriculum_reference_sources(publisher="Unknown Publisher") == []


def test_subject_filter_can_identify_bible_worldview_sources():
    bible = get_curriculum_reference_sources(subject="Bible")
    assert any(source.publisher == "Purposeful Design" for source in bible)
    assert any(source.publisher == "Positive Action for Christ" for source in bible)
    assert any(source.publisher == "Summit Ministries" for source in bible)


def test_registry_distinguishes_true_publisher_maps_from_scope_sequences():
    map_sources = [
        source for source in CURRICULUM_REFERENCE_SOURCES
        if source.mapping_resource_level == "publisher_map"
    ]
    assert {source.publisher for source in map_sources} >= {
        "BJU Press",
        "Purposeful Design",
        "Positive Action for Christ",
    }

    abeka = get_curriculum_reference_sources(publisher="Abeka")
    assert abeka
    assert all(source.mapping_resource_level != "publisher_map" for source in abeka)

    summit = get_curriculum_reference_sources(publisher="Summit Ministries")
    assert summit
    assert all(source.mapping_resource_level != "publisher_map" for source in summit)
