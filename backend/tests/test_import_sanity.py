import core


def test_core_import_points_to_backend():
    """Guardrail: ensure 'core' resolves to backend/core, not a repo-root shadowing package."""
    assert r"\backend\core\__init__.py" in core.__file__.replace("/", "\\"), (
        f"core imported from wrong location: {core.__file__}. "
        "Should be backend/core. Check for module shadowing."
    )
