#!/usr/bin/env python3
"""Generate immutable review packets for governance policy adjudication.

Purpose:
    Create deterministic, auditable review packets for each drifted policy.
    Each packet contains canonical baseline, current content, diff, and decision records.

Design:
    - Deterministic: sorted files, LF-only, UTF-8, reproducible ordering
    - Immutable: append-only history, no overwrites
    - Auditable: full diff, classification, adjudication trail
    - Governance: tracks ACCEPT_DRIFT, REJECT_DRIFT, REQUIRES_ESCALATION decisions

Lifecycle:
    1. Generate packet from canonical + current
    2. Perform manual adjudication (governance decision)
    3. Record decision as immutable DECISION.json
    4. Freeze until all policies adjudicated
    5. Refresh baselines only after all decisions finalized
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from env_guard import validate_environment
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run command and return exit code and stdout."""
    proc = subprocess.run(
        args,
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout


def generate_diff(original: str, current: str) -> str:
    """Generate unified diff between original and current content."""
    rc, diff = run_cmd(
        ["diff", "-u", "--color=never", "-", "-"],
        cwd=Path.cwd(),
    )
    # Use pipes for diff
    proc = subprocess.run(
        ["diff", "-u", "--color=never"],
        input=f"{original}\n{current}",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout if proc.stdout else "(no differences)"


def read_file_lf_only(path: Path) -> str:
    """Read file as-is, preserving actual line endings (binary mode)."""
    if not path.exists():
        return ""
    # Read in binary mode to preserve actual line endings
    content_bytes = path.read_bytes()
    return content_bytes.decode("utf-8")


def read_file_normalized(path: Path) -> str:
    """Read file and normalize to LF only."""
    if not path.exists():
        return ""
    # Read in binary mode to preserve actual line endings
    content_bytes = path.read_bytes()
    content = content_bytes.decode("utf-8")
    # Normalize line endings to LF
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Ensure trailing newline
    if content and not content.endswith("\n"):
        content += "\n"
    return content


def classify_drift(original: str, current: str) -> dict:
    """Analyze drift and classify type."""
    # Calculate metrics first
    orig_size = len(original)
    curr_size = len(current)
    size_diff = curr_size - orig_size
    size_ratio = size_diff / orig_size if orig_size > 0 else 0.0

    orig_lines = len(original.splitlines())
    curr_lines = len(current.splitlines())
    line_diff = curr_lines - orig_lines

    is_reduction = curr_size < orig_size
    is_expansion = curr_size > orig_size

    if original == current:
        classification = "NO_DRIFT"
    # Classify based on magnitude
    elif is_reduction and abs(size_ratio) > 0.5:
        classification = "SIGNIFICANT_REDUCTION"
    elif is_expansion and size_ratio > 0.5:
        classification = "SIGNIFICANT_EXPANSION"
    elif is_reduction:
        classification = "MINOR_REDUCTION"
    elif is_expansion:
        classification = "MINOR_EXPANSION"
    else:
        classification = "CONTENT_DRIFT"

    return {
        "classification": classification,
        "byte_diff_count": abs(size_diff),
        "line_diff_count": abs(line_diff),
        "reduction_magnitude": abs(size_ratio) if is_reduction else 0.0,
        "expansion_magnitude": size_ratio if is_expansion else 0.0,
        "original_size_bytes": orig_size,
        "current_size_bytes": curr_size,
        "original_lines": orig_lines,
        "current_lines": curr_lines,
    }


def generate_review_packet(
    policy_name: str,
    canonical_path: Path,
    current_path: Path,
    review_dir: Path,
) -> None:
    """Generate immutable review packet."""
    print(f"\nGenerating review packet for {policy_name}...")

    # Read files - preserve actual content for packets, normalize for comparison
    original_actual = read_file_lf_only(canonical_path)
    current_actual = read_file_lf_only(current_path)

    # Normalize for comparison and drift classification
    original_normalized = read_file_normalized(canonical_path)
    current_normalized = read_file_normalized(current_path)

    # Generate diff
    diff = subprocess.run(
        ["diff", "-u", "--color=never", canonical_path, current_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout

    # Classify drift using normalized versions
    drift_info = classify_drift(original_normalized, current_normalized)

    # Timestamps
    now = datetime.now(timezone.utc)
    iso_timestamp = now.isoformat()

    # Write packet files - preserve actual file content (including line endings)
    (review_dir / "ORIGINAL_BASELINE.txt").write_text(original_actual, encoding="utf-8")
    (review_dir / "CURRENT_CONTENT.txt").write_text(current_actual, encoding="utf-8")
    (review_dir / "DIFF.txt").write_text(diff, encoding="utf-8")

    # Drift classification
    drift_json = {
        "policy_name": policy_name,
        "review_generated_utc": iso_timestamp,
        "canonical_source": str(canonical_path),
        "current_source": str(current_path),
        **drift_info,
    }
    (review_dir / "DRIFT_CLASSIFICATION.json").write_text(
        json.dumps(drift_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Adjudication template
    adjudication_md = f"""# Adjudication Record: {policy_name}

**Review Generated:** {iso_timestamp}
**Canonical Source:** {canonical_path}
**Current Source:** {current_path}

## Drift Summary

- **Classification:** {drift_info['classification']}
- **Original Size:** {drift_info['original_size_bytes']:,} bytes ({drift_info['original_lines']} lines)
- **Current Size:** {drift_info['current_size_bytes']:,} bytes ({drift_info['current_lines']} lines)
- **Byte Difference:** {drift_info['byte_diff_count']:,} bytes
- **Line Difference:** {drift_info['line_diff_count']:,} lines

## Review Questions

1. **Is this drift intentional?**
   - Intentional policy changes require approval authority
   - Accidental drift indicates process failure

2. **Who authorized this change?**
   - List responsible parties and approval dates
   - If not approved, note escalation required

3. **What is the operational risk?**
   - Security impact
   - Compliance impact
   - Functional impact

4. **Is this acceptable?**
   - ACCEPT_DRIFT: Intentional, approved, acceptable
   - REJECT_DRIFT: Requires revert to canonical
   - REQUIRES_ESCALATION: Needs higher authority review

## Adjudication Notes

(To be filled by governance review board)

---

## Files for Reference

- ORIGINAL_BASELINE.txt: Canonical version
- CURRENT_CONTENT.txt: Current version
- DIFF.txt: Unified diff

See DECISION.json for final decision record.
"""
    (review_dir / "ADJUDICATION.md").write_text(adjudication_md, encoding="utf-8")

    # Decision template (empty, filled by adjudication)
    decision_json = {
        "decision_state": "PENDING",
        "policy_name": policy_name,
        "review_generated_utc": iso_timestamp,
        "adjudication_utc": None,
        "adjudicated_by": None,
        "decision": None,
        "justification": None,
        "escalation_required": False,
        "escalation_target": None,
    }
    (review_dir / "DECISION.json").write_text(
        json.dumps(decision_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        f"✓ Review packet generated: {review_dir}"
    )
    print(
        f"  - ORIGINAL_BASELINE.txt: {drift_info['original_size_bytes']:,} bytes"
    )
    print(
        f"  - CURRENT_CONTENT.txt: {drift_info['current_size_bytes']:,} bytes"
    )
    print(f"  - DIFF.txt: {len(diff)} bytes")
    print(f"  - DRIFT_CLASSIFICATION.json: {drift_info['classification']}")
    print(f"  - ADJUDICATION.md: (template for review board)")
    print(f"  - DECISION.json: (pending decision)")


def main() -> int:
    validate_environment()
    parser = argparse.ArgumentParser(
        description="Generate immutable review packets for policy adjudication"
    )
    parser.add_argument(
        "policy",
        nargs="?",
        help="Policy name (all policies if omitted)",
        choices=["all", "api", "compliance", "demo", "recovery"],
    )

    args = parser.parse_args()
    policy = args.policy or "all"

    root = Path.cwd()
    review_base = root / "solomon_governance_c1" / "governance" / "c1" / "reviews"

    # Define policies: (name, canonical_source, current_source)
    # Canonical = APPROVED_CANONICAL baseline (certified, in docs/)
    # Current = CONTENT_REDUCED version (in c1_candidate_sources/)
    policies = {
        "api": (
            "API_VERSION_POLICY",
            root / "docs" / "API_VERSION_POLICY.md",
            root / "solomon_governance_c1" / "c1_candidate_sources" / "API_VERSION_POLICY.md",
        ),
        "compliance": (
            "CROWN_IP_COMPLIANCE_POLICY",
            root / "docs" / "CROWN_IP_COMPLIANCE_POLICY.md",
            root / "solomon_governance_c1" / "c1_candidate_sources" / "CROWN_IP_COMPLIANCE_POLICY.md",
        ),
        "demo": (
            "DEMO_MODE_POLICY",
            root / "docs" / "DEMO_MODE_POLICY.md",
            root / "solomon_governance_c1" / "c1_candidate_sources" / "DEMO_MODE_POLICY.md",
        ),
        "recovery": (
            "DISASTER_RECOVERY_POLICY",
            root / "docs" / "DISASTER_RECOVERY_POLICY.md",
            root / "solomon_governance_c1" / "c1_candidate_sources" / "DISASTER_RECOVERY_POLICY.md",
        ),
    }

    # Generate packets
    to_generate = (
        list(policies.keys()) if policy == "all" else [policy]
    )

    print(f"\nGenerating review packets for {len(to_generate)} policies...")

    for p in to_generate:
        if p not in policies:
            print(f"ERROR: Unknown policy {p}")
            return 1

        policy_name, canonical, current = policies[p]
        review_dir = (
            review_base / f"REVIEW_2026_05_15_{policy_name.replace(' ', '_')}"
        )
        review_dir.mkdir(parents=True, exist_ok=True)

        if not canonical.exists():
            print(f"WARNING: Canonical not found: {canonical}")
            print(f"         Skipping {policy_name}")
            continue

        if not current.exists():
            print(f"WARNING: Current not found: {current}")
            print(f"         Skipping {policy_name}")
            continue

        generate_review_packet(policy_name, canonical, current, review_dir)

    return 0


if __name__ == "__main__":
    exit(main())
