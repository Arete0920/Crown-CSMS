from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "secrets-control-drill.yml"


def test_secrets_control_drill_is_non_production_and_fail_closed():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "routine_rotation" in workflow
    assert "failed_rotation" in workflow
    assert "break_glass" in workflow
    assert "production|prod|live" in workflow
    assert "this drill is non-production only" in workflow
    assert "steps.decision.outputs.result == 'FAIL'" in workflow
    assert "exit 1" in workflow


def test_secrets_control_drill_requires_audit_revocation_and_validation():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required_input in (
        "actor_identity",
        "approver_identity",
        "audit_event_available",
        "old_access_revoked",
        "validation_passed",
        "prior_secret_suspected_compromised",
    ):
        assert required_input in workflow

    assert "capture_sanitized_audit_evidence" in workflow
    assert "revoke_prior_or_emergency_access" in workflow
    assert "restore_service_health_and_repeat_validation" in workflow
    assert "do_not_restore_prior_secret" in workflow


def test_secrets_control_drill_emits_sanitized_immutable_evidence():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert '"workflow_sha": "${GITHUB_SHA}"' in workflow
    assert '"secret_value_recorded": false' in workflow
    assert '"production_mutation_performed": false' in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "retention-days: 30" in workflow
    assert "Secret value recorded: false" in workflow
    assert "Production mutation performed: false" in workflow
