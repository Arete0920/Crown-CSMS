import json
from pathlib import Path

from tools.validate_recovery_evidence import validate


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "docs" / "recovery" / "recovery-evidence.example.json"


def _example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_recovery_evidence_is_valid_and_sanitized():
    assert validate(_example()) == []


def test_missing_required_section_fails_closed():
    payload = _example()
    del payload["restore_drill"]
    errors = validate(payload)
    assert any("restore_drill" in error for error in errors)


def test_failed_or_incomplete_drills_are_rejected():
    payload = _example()
    payload["rollback_drill"]["result"] = "fail"
    payload["restore_drill"]["isolated_environment"] = False
    errors = validate(payload)
    assert "rollback_drill.result must be pass" in errors
    assert "restore_drill.isolated_environment must be true" in errors


def test_integrity_anomalies_are_rejected():
    payload = _example()
    payload["integrity_validation"]["cross_tenant_anomalies"] = 1
    payload["integrity_validation"]["missing_records"] = 2
    errors = validate(payload)
    assert "integrity_validation.cross_tenant_anomalies must equal 0" in errors
    assert "integrity_validation.missing_records must equal 0" in errors


def test_measured_objectives_must_meet_accepted_targets():
    payload = _example()
    payload["rto_rpo"]["measured_rto_minutes"] = 45
    payload["rto_rpo"]["accepted_rto_minutes"] = 30
    errors = validate(payload)
    assert "measured RTO exceeds accepted RTO" in errors


def test_credential_bearing_fields_are_rejected():
    payload = _example()
    payload["restore_drill"]["database_url"] = "not-allowed"
    errors = validate(payload)
    assert any("forbidden credential-bearing field" in error for error in errors)


def test_rejected_approval_does_not_close_evidence():
    payload = _example()
    payload["approvals"][0]["decision"] = "rejected"
    errors = validate(payload)
    assert "approvals[0].decision must be approved" in errors
