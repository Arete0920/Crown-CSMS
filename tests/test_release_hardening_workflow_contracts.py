from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROD_WORKFLOW = ROOT / ".github" / "workflows" / "deploy-prod.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_prod_release_identity_uses_deploy_sha():
    text = _read(PROD_WORKFLOW)
    assert "EXPECTED_SHA: ${{ steps.vars.outputs.deploy_sha }}" in text


def test_prod_has_sarif_capability_gate():
    text = _read(PROD_WORKFLOW)
    assert "name: Detect code scanning availability (SARIF gate)" in text
    assert "id: sarif_gate" in text


def test_prod_sarif_upload_is_conditionally_gated():
    text = _read(PROD_WORKFLOW)
    assert "if: ${{ always() && steps.sarif_gate.outputs.can_upload == 'true' }}" in text
    assert "if: false" not in text


def test_prod_removed_redundant_verification_steps():
    text = _read(PROD_WORKFLOW)
    assert "name: Verify deployed build_sha via /api/health/" not in text
    assert "name: Verify live production build" not in text


def test_prod_applies_appsettings_before_integrity_probe():
    text = _read(PROD_WORKFLOW)
    assert text.index('name: Apply appsettings (allowlisted only)') < text.index('name: Verify tenant-aware integrity')


def test_prod_health_check_uses_extended_backoff_window():
    text = _read(PROD_WORKFLOW)
    assert "MAX_ATTEMPTS=20" in text
    assert "sha_matches() {" in text
    assert "elif sha_matches \"$BUILD_SHA\" \"$EXPECTED_SHA\"; then" in text
    assert "[[ \"$BUILD_SHA\" == *\"$EXPECTED_SHA\"* ]]" not in text
