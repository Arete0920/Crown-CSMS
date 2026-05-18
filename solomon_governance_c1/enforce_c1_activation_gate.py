#!/usr/bin/env python3
"""SOLOMON C1 fail-closed activation gate enforcer.

Binary result:
- ALLOW (all checks pass)
- DENY (any check fails)

This script does not activate anything. It only decides if activation is allowed.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "c1"
REG = GOV / "registers"
SIM = GOV / "simulation"
CERT = GOV / "certification"
GATE = GOV / "gates"

DECISION_REGISTER = REG / "decision_register.csv"
RISK_EXCEPTIONS = REG / "risk_exceptions.csv"
CERT_RESULT = CERT / "CERTIFICATION_RESULT.json"
GOLDEN_MANIFEST = GOV / "golden" / "golden_corpus_manifest.csv"


@dataclass
class GateCheck:
    name: str
    required: bool
    passed: bool
    details: str


@dataclass
class GateDecision:
    requested_capability: str
    decision: str
    checks: list[GateCheck]


def _run(script_name: str) -> tuple[bool, str]:
    script = ROOT / script_name
    if not script.exists():
        return False, f"missing script: {script_name}"
    res = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    ok = res.returncode == 0
    msg = (res.stdout + "\n" + res.stderr).strip()
    return ok, msg


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_approved_canonical() -> int:
    if not DECISION_REGISTER.exists():
        return 0
    with DECISION_REGISTER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return sum(1 for r in rows if (r.get("decision") or "").strip() == "APPROVED_CANONICAL")


def _count_quarantine_open() -> int:
    if not RISK_EXCEPTIONS.exists():
        return 0
    with RISK_EXCEPTIONS.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    # Any non-empty row is considered unresolved until explicitly handled by human decision process.
    return len(rows)


def evaluate(capability: str) -> GateDecision:
    checks: list[GateCheck] = []

    # 1) validator pass
    ok, msg = _run("verify_c1_control_plane.py")
    checks.append(GateCheck("validator_pass", True, ok, msg.splitlines()[-1] if msg else ""))

    # 2) deterministic simulation pass
    sim_ok, sim_msg = _run("simulate_c1_ingestion_manifest.py")
    checks.append(GateCheck("simulation_pass", True, sim_ok, sim_msg.splitlines()[-1] if sim_msg else ""))

    # 3) reproducibility confirmation
    diff_ok, diff_msg = _run("verify_c1_artifact_diff.py")
    checks.append(GateCheck("reproducibility_confirmation", True, diff_ok, diff_msg.splitlines()[-1] if diff_msg else ""))

    # 4) golden corpus stability
    golden_ok, golden_msg = _run("verify_c1_golden_corpus.py")
    checks.append(GateCheck("golden_corpus_stable", True, golden_ok, golden_msg.splitlines()[-1] if golden_msg else ""))

    # 5) human approval record exists
    approved = _count_approved_canonical()
    checks.append(
        GateCheck(
            "human_approval_record",
            True,
            approved > 0,
            f"APPROVED_CANONICAL count={approved}",
        )
    )

    # 6) clean quarantine state (for activation, unresolved risk rows block)
    q_open = _count_quarantine_open()
    checks.append(
        GateCheck(
            "clean_quarantine_state",
            True,
            q_open == 0,
            f"unresolved_risk_exception_rows={q_open}",
        )
    )

    # 7) trusted deterministic certification (cycles 1-3)
    cert_pass = False
    cert_details = "missing CERTIFICATION_RESULT.json"
    if CERT_RESULT.exists():
        try:
            payload = _load_json(CERT_RESULT)
            cert_pass = (payload.get("final_result") == "TRUSTED")
            cert_details = f"final_result={payload.get('final_result')}"
        except Exception as exc:  # pragma: no cover - defensive
            cert_details = f"invalid certification result: {exc}"
    checks.append(GateCheck("deterministic_certification", True, cert_pass, cert_details))

    allow = all(c.passed for c in checks if c.required)
    decision = "ALLOW" if allow else "DENY"
    return GateDecision(requested_capability=capability, decision=decision, checks=checks)


def main() -> None:
    capability = sys.argv[1] if len(sys.argv) > 1 else "ingestion"
    decision = evaluate(capability)

    GATE.mkdir(parents=True, exist_ok=True)
    out = GATE / f"{capability}_activation_gate.json"
    out.write_text(
        json.dumps(
            {
                "requested_capability": decision.requested_capability,
                "decision": decision.decision,
                "checks": [asdict(c) for c in decision.checks],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(decision.decision)
    print(f"gate_report={out}")
    for c in decision.checks:
        state = "PASS" if c.passed else "FAIL"
        print(f"- {c.name}: {state} ({c.details})")

    if decision.decision != "ALLOW":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
