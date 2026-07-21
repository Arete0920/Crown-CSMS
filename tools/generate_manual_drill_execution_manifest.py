from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOLO_MAINTAINER_IDENTITY = "founder-product-owner"
GOVERNANCE_BOUNDARY = (
    "solo-maintainer administrative authorization; not independent approval or witnessing"
)


def build_manifest(failed_candidate_sha: str, last_known_good_sha: str) -> dict:
    failures = []
    for name, value in (
        ("failed_candidate_sha", failed_candidate_sha),
        ("last_known_good_sha", last_known_good_sha),
    ):
        if not SHA_RE.fullmatch(value):
            failures.append(f"{name} must be 40 lowercase hexadecimal characters")
    if failed_candidate_sha == last_known_good_sha:
        failures.append("failed candidate and last-known-good SHA must differ")

    secrets_identity_inputs = {
        "actor_identity": SOLO_MAINTAINER_IDENTITY,
        "approver_identity": SOLO_MAINTAINER_IDENTITY,
        "audit_event_available": True,
        "old_access_revoked": True,
        "validation_passed": True,
        "prior_secret_suspected_compromised": False,
    }
    executions = [
        {
            "name": "recovery_decision_unhealthy_runtime",
            "workflow": "recovery-control-drill.yml",
            "environment": "non-production",
            "inputs": {
                "failed_candidate_sha": failed_candidate_sha,
                "last_known_good_sha": last_known_good_sha,
                "runtime_health": "unhealthy",
                "immutable_image_available": True,
                "restore_evidence_available": False,
            },
            "expected_result": "PASS",
            "production_mutation_performed": False,
        },
        {
            "name": "secrets_routine_rotation",
            "workflow": "secrets-control-drill.yml",
            "environment": "staging",
            "inputs": {
                "scenario": "routine_rotation",
                "environment_name": "staging",
                **secrets_identity_inputs,
            },
            "expected_result": "PASS",
            "production_mutation_performed": False,
        },
        {
            "name": "secrets_failed_rotation_recovery",
            "workflow": "secrets-control-drill.yml",
            "environment": "staging",
            "inputs": {
                "scenario": "failed_rotation",
                "environment_name": "staging",
                **secrets_identity_inputs,
            },
            "expected_result": "PASS",
            "production_mutation_performed": False,
        },
        {
            "name": "secrets_break_glass",
            "workflow": "secrets-control-drill.yml",
            "environment": "staging",
            "inputs": {
                "scenario": "break_glass",
                "environment_name": "staging",
                **secrets_identity_inputs,
            },
            "expected_result": "PASS",
            "production_mutation_performed": False,
        },
    ]

    return {
        "schema_version": 1,
        "mode": "manual_nonproduction_drill_execution_manifest",
        "execution_performed": False,
        "production_mutation_performed": False,
        "independent_approval_present": False,
        "governance_boundary": GOVERNANCE_BOUNDARY,
        "workflow_ref": "main",
        "failures": sorted(failures),
        "execution_count": len(executions),
        "executions": executions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate validated non-production manual drill execution inputs.")
    parser.add_argument("--failed-candidate-sha", required=True)
    parser.add_argument("--last-known-good-sha", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = build_manifest(args.failed_candidate_sha, args.last_known_good_sha)
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if manifest["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
