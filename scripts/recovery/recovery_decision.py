#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class RecoveryDecision:
    decision: str
    action: str
    result: str
    manual_intervention: bool
    database_restore_required: bool
    production_mutation_performed: bool = False


def evaluate(runtime_health: str, immutable_image_available: bool, restore_evidence_available: bool) -> RecoveryDecision:
    if runtime_health not in {"healthy", "unhealthy", "unavailable"}:
        raise ValueError(f"unsupported runtime health: {runtime_health}")
    if runtime_health == "healthy":
        return RecoveryDecision(
            "skip_application_rollback",
            "preserve_current_runtime_and_investigate_deploy_automation",
            "PASS",
            False,
            False,
        )
    if immutable_image_available:
        return RecoveryDecision(
            "restore_immutable_last_known_good_image",
            "restore_exact_image_then_verify_identity_health_database_and_tenant_integrity",
            "PASS",
            False,
            False,
        )
    if restore_evidence_available:
        return RecoveryDecision(
            "manual_application_recovery_with_restore_fallback",
            "enter_manual_incident_control_and_use_approved_restore_procedure_if_required",
            "PASS_WITH_MANUAL_CONTROL",
            True,
            False,
        )
    return RecoveryDecision(
        "stop_and_escalate",
        "do_not_claim_recovery_until_immutable_rollback_or_restore_fallback_is_proven",
        "FAIL",
        True,
        True,
    )


def validate_sha(value: str, label: str) -> None:
    if not SHA_RE.fullmatch(value):
        raise ValueError(f"{label} must be a full 40-character lowercase hexadecimal SHA")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-sha", required=True)
    parser.add_argument("--failed-candidate-sha", required=True)
    parser.add_argument("--last-known-good-sha", required=True)
    parser.add_argument("--runtime-health", required=True, choices=("healthy", "unhealthy", "unavailable"))
    parser.add_argument("--immutable-image-available", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--restore-evidence-available", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    started = time.perf_counter()
    validate_sha(args.repository_sha, "repository SHA")
    validate_sha(args.failed_candidate_sha, "failed candidate SHA")
    validate_sha(args.last_known_good_sha, "last-known-good SHA")
    if args.failed_candidate_sha == args.last_known_good_sha:
        raise ValueError("failed candidate and last-known-good SHA must differ")

    decision = evaluate(args.runtime_health, args.immutable_image_available, args.restore_evidence_available)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    packet = {
        "schema_version": 1,
        "repository_sha": args.repository_sha,
        "failed_candidate_sha": args.failed_candidate_sha,
        "last_known_good_sha": args.last_known_good_sha,
        "runtime_health": args.runtime_health,
        "immutable_image_available": args.immutable_image_available,
        "restore_evidence_available": args.restore_evidence_available,
        "control_elapsed_ms": elapsed_ms,
        **asdict(decision),
        "scope_boundary": "Decision-control simulation only; no Azure or production mutation.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, sort_keys=True))
    return 1 if decision.result == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
