import json
from pathlib import Path

from tools.validate_recovery_closure_evidence import validate_closure


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "docs" / "recovery" / "recovery-evidence.example.json"


def _example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_documentation_example_is_rejected_for_closure():
    errors = validate_closure(_example())
    assert "release_sha cannot be a template placeholder" in errors
    assert any("drill_id cannot be a template placeholder" in error for error in errors)
    assert any("must identify operational evidence" in error for error in errors)
    assert "rto_rpo.accepted_by must identify the accepting authority" in errors
    assert any("must identify the operator" in error for error in errors)
    assert any("must identify the approving person" in error for error in errors)


def test_operationally_identified_evidence_can_pass_closure_validation():
    payload = _example()
    payload["release_sha"] = "a" * 40
    payload["rollback_drill"]["drill_id"] = "RECOVERY-20260728-ROLLBACK"
    payload["rollback_drill"]["from_sha"] = "b" * 40
    payload["rollback_drill"]["to_sha"] = "a" * 40
    payload["rollback_drill"]["evidence_reference"] = "change-record-CR-20260728-001"
    payload["restore_drill"]["drill_id"] = "RECOVERY-20260728-RESTORE"
    payload["restore_drill"]["evidence_reference"] = "restore-record-RR-20260728-001"
    payload["rto_rpo"]["accepted_by"] = "Founder/Product Owner"
    payload["operators"][0]["name"] = "Named Platform Operator"
    payload["approvals"][0]["name"] = "Named Product Owner"

    assert validate_closure(payload) == []
