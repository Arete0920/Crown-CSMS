from pathlib import Path


def _api_v1_urls_source() -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / 'crown_api' / 'api_v1_urls.py').read_text(encoding='utf-8')


def test_specific_module_includes_appear_before_legacy_catch_all_include():
    source = _api_v1_urls_source()

    idx_financial_aid = source.index('path("financial-aid/", include("financial_aid.urls"))')
    idx_board = source.index('path("board/", include("board_oversight.urls"))')
    idx_hr = source.index('path("hr/", include("hr.urls"))')
    idx_advancement = source.index('path("advancement/", include("advancement.urls"))')
    idx_legacy = source.index('path("", include("crown_api.api_urls"))')

    assert idx_financial_aid < idx_legacy
    assert idx_board < idx_legacy
    assert idx_hr < idx_legacy
    assert idx_advancement < idx_legacy


def test_academics_include_precedes_legacy_catch_all_include():
    source = _api_v1_urls_source()

    idx_academics = source.index('path("", include("academics.urls"))')
    idx_legacy = source.index('path("", include("crown_api.api_urls"))')

    assert idx_academics < idx_legacy
