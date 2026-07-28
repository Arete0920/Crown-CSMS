import json
from pathlib import Path

from tools.validate_secret_store_evidence import validate


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "docs" / "security" / "secret-store-evidence.example.json"


def _example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_template_is_valid_only_when_placeholders_are_allowed():
    assert validate(_example(), allow_placeholders=True) == []
    errors = validate(_example())
    assert "release_sha cannot be the template placeholder" in errors
    assert any("exercise_id cannot be a template placeholder" in error for error in errors)
    assert any("name must identify the approving person" in error for error in errors)


def test_missing_required_fields_fail_closed():
    payload = _example()
    del payload["runtime_identity"]
    errors = validate(payload, allow_placeholders=True)
    assert any("runtime_identity" in error for error in errors)


def test_secret_bearing_fields_are_rejected():
    payload = _example()
    payload["secret_store"]["client_secret"] = "not-allowed"
    errors = validate(payload, allow_placeholders=True)
    assert any("forbidden secret-bearing field" in error for error in errors)


def test_private_key_material_is_rejected():
    payload = _example()
    payload["audit_sample"]["notes"] = "-----BEGIN PRIVATE KEY-----"
    errors = validate(payload, allow_placeholders=True)
    assert any("private key material" in error for error in errors)


def test_weak_operational_evidence_is_rejected():
    payload = _example()
    payload["runtime_identity"]["least_privilege"] = False
    payload["rotation_exercise"]["old_access_revoked"] = False
    errors = validate(payload, allow_placeholders=True)
    assert "runtime_identity.least_privilege must be true" in errors
    assert "rotation_exercise.old_access_revoked must be true" in errors
