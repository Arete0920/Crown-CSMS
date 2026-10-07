from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_STATUS = ROOT / "audit-artifacts" / "wizard-e2e-evidence" / "latest" / "99_STATUS.json"

LEGACY_SCORE_SCRIPT = ROOT / "scripts" / "execution" / "121_50_wizard_deep_dive_assessment.ps1"
WIZARD_WORKFLOW = ROOT / ".github" / "workflows" / "wizard-e2e-evidence-gate.yml"

FALSE_COMPLETION_PATTERNS = (
    re.compile(r"all\s+50\s+wizards\s+are\s+complete\s+and\s+proof-backed", re.I),
    re.compile(r"50\s*/\s*50.*proof[- ]backed", re.I),
)


def load_status() -> dict:
    if not EVIDENCE_STATUS.exists():
        raise SystemExit(f"missing wizard evidence status: {EVIDENCE_STATUS}")
    return json.loads(EVIDENCE_STATUS.read_text(encoding="utf-8"))


def legacy_structural_score_is_not_functional_proof() -> list[str]:
    failures: list[str] = []
    if not LEGACY_SCORE_SCRIPT.exists():
        failures.append(f"missing legacy assessment script: {LEGACY_SCORE_SCRIPT}")
        return failures

    text = LEGACY_SCORE_SCRIPT.read_text(encoding="utf-8", errors="replace")
    if "if ($Row.HasTests) { $score++ }" in text:
        failures.append(
            "legacy 50-wizard score awards structural credit for HasTests; "
            "that score must not be interpreted as LIVE_UI_API/BACKEND_PERSISTENCE/RBAC_TENANT proof"
        )
    return failures


def stale_completion_claims() -> list[str]:
    failures: list[str] = []
    if not WIZARD_WORKFLOW.exists():
        return failures
    text = WIZARD_WORKFLOW.read_text(encoding="utf-8", errors="replace")
    for pattern in FALSE_COMPLETION_PATTERNS:
        if pattern.search(text):
            failures.append(
                f"{WIZARD_WORKFLOW.relative_to(ROOT)} still contains an unconditional 50-wizard proof-backed completion claim"
            )
            break
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fail-on-stale-claims",
        action="store_true",
        help="fail when legacy scoring/claims can still be mistaken for live functional certification",
    )
    args = parser.parse_args()

    status = load_status()
    all_proof_backed = bool(status.get("all_canonical_wizards_proof_backed", False))
    placeholder_count = int(status.get("placeholder_count", 0))
    missing_count = int(status.get("missing_count", 0))
    proof_backed_count = int(status.get("proof_backed_count", 0))
    canonical_count = int(status.get("canonical_registered_count", 0))
    duplicate_alias_count = int(status.get("duplicate_alias_count", 0))
    nonregistered_scope_count = int(status.get("nonregistered_scope_count", 0))

    structural_warnings = legacy_structural_score_is_not_functional_proof()
    stale_claims = stale_completion_claims()

    report = {
        "schema_version": 2,
        "canonical_registered_count": canonical_count,
        "placeholder_count": placeholder_count,
        "missing_count": missing_count,
        "proof_backed_count": proof_backed_count,
        "all_canonical_wizards_proof_backed": all_proof_backed,
        "excluded_duplicate_alias_count": duplicate_alias_count,
        "excluded_nonregistered_scope_count": nonregistered_scope_count,
        "legacy_structural_score_warnings": structural_warnings,
        "stale_completion_claims": stale_claims,
        "functional_completion_status": "PASS" if all_proof_backed else "NOT_VERIFIED",
    }

    out_dir = EVIDENCE_STATUS.parent
    (out_dir / "98_CLAIMS_GUARD.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Wizard Completion Claims Guard",
        "",
        f"- Functional completion: **{report['functional_completion_status']}**",
        f"- Canonical registered wizards: **{canonical_count}**",
        f"- Proof-backed canonical wizards: **{proof_backed_count}/{canonical_count}**",
        f"- Canonical placeholders: **{placeholder_count}**",
        f"- Missing canonical specs: **{missing_count}**",
        f"- Excluded duplicate aliases: **{duplicate_alias_count}**",
        f"- Excluded nonregistered conceptual specs: **{nonregistered_scope_count}**",
        "",
        "Structural inventory, file presence, registry coverage, scaffold/browser-shell proof, and legacy HasTests scoring are not substitutes for live functional evidence.",
        "The broader 50-row conceptual inventory is not the canonical registered-wizard completion denominator.",
    ]
    if structural_warnings:
        lines.extend(["", "## Legacy structural-score warnings", *[f"- {item}" for item in structural_warnings]])
    if stale_claims:
        lines.extend(["", "## Stale completion claims", *[f"- {item}" for item in stale_claims]])
    (out_dir / "98_CLAIMS_GUARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))

    if args.fail_on_stale_claims and not all_proof_backed and (structural_warnings or stale_claims):
        print("ERROR: legacy structural scoring or completion claims conflict with current canonical live functional evidence")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
