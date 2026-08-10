from academics.curriculum_publishers import (
    PUBLISHER_PROFILES,
    get_curriculum_publisher_profile,
    normalize_curriculum_publisher,
    publisher_search_terms,
)


def test_normalizes_canonical_names_and_aliases():
    assert normalize_curriculum_publisher("BJU Press") == "BJU Press"
    assert normalize_curriculum_publisher("bob jones university press") == "BJU Press"
    assert normalize_curriculum_publisher("A Beka") == "Abeka"
    assert normalize_curriculum_publisher("standard press") == "Standard Publishing"


def test_normalizes_aliases_inside_descriptive_labels_without_partial_word_false_positives():
    assert normalize_curriculum_publisher("BJU Press Biology 7") == "BJU Press"
    assert normalize_curriculum_publisher("Summit worldview curriculum") == "Summit Ministries"
    assert normalize_curriculum_publisher("space science") == ""
    assert normalize_curriculum_publisher("capacity planning") == ""


def test_unknown_and_blank_values_remain_unclassified():
    assert normalize_curriculum_publisher("") == ""
    assert normalize_curriculum_publisher("Unknown Vendor") == ""
    assert get_curriculum_publisher_profile("Unknown Vendor") is None


def test_profiles_are_metadata_only_and_do_not_claim_live_integrations():
    for profile in PUBLISHER_PROFILES.values():
        assert profile.integration_status in {"metadata_only", "legacy_metadata_only"}
        assert "licensed_content" in profile.content_policy or "ownership_and_license" in profile.content_policy


def test_search_terms_preserve_unknown_query_and_expand_known_publishers():
    assert publisher_search_terms("Unknown Vendor") == ["Unknown Vendor"]
    terms = publisher_search_terms("BJU")
    assert terms[0] == "BJU Press"
    assert "bju" in terms
