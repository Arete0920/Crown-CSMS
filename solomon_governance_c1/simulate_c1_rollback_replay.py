#!/usr/bin/env python3
"""
SOLOMON C1 Rollback Replay Simulator

Purpose:
  Simulate rollback determinism without mutating canonical governance state.

Rules:
  - Read canonical simulation manifests.
  - Read runtime rollback manifest.
  - Build source -> derived artifact lineage.
  - Simulate removal/unwind in runtime only.
  - Emit deterministic rollback replay report.
  - Never write to governance/c1/simulation, governance/c1/rollback, or canonical dirs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.cwd()
GOV = ROOT / "governance" / "c1"
SIM = GOV / "simulation"
RUNTIME = GOV / "runtime"
RUNTIME_ROLLBACK = RUNTIME / "rollback"
ROLLBACK_RUNTIME = RUNTIME / "rollback_runtime"

INGESTION_MANIFEST = SIM / "ingestion_simulation_manifest.csv"
PROVENANCE_MANIFEST = SIM / "provenance_inheritance_manifest.csv"
QUARANTINE_MANIFEST = SIM / "quarantine_propagation_manifest.csv"
ROLLBACK_MANIFEST = RUNTIME_ROLLBACK / "rollback_manifest.csv"

REPLAY_REPORT = ROLLBACK_RUNTIME / "rollback_replay_report.json"
REPLAY_GRAPH = ROLLBACK_RUNTIME / "rollback_lineage_graph.json"


def fail(message: str) -> None:
    print(f"FAILED: {message}")
    sys.exit(1)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_hash_json(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_text(encoded)


def source_id(row: dict) -> str:
    sid = row.get("source_id", "").strip()
    if not sid:
        fail(f"row missing source_id: {row}")
    return sid


def derived_id(row: dict) -> str:
    value = (
        row.get("derived_artifact_id")
        or row.get("simulated_artifact_id")
        or row.get("chunk_id")
        or ""
    ).strip()
    return value


def build_lineage_graph(
    ingestion_rows: list[dict],
    provenance_rows: list[dict],
    quarantine_rows: list[dict],
    rollback_rows: list[dict],
) -> dict:
    graph: dict[str, dict] = {}

    for row in ingestion_rows:
        sid = source_id(row)
        graph.setdefault(
            sid,
            {
                "source_id": sid,
                "custody_path": row.get("custody_path", ""),
                "integrity_reference": row.get("integrity_reference") or row.get("sha256", ""),
                "derived_artifacts": [],
                "quarantine_events": [],
                "rollback_actions": [],
            },
        )

    for row in provenance_rows:
        sid = source_id(row)
        if sid not in graph:
            fail(f"provenance references unknown source_id={sid}")
        artifact_id = derived_id(row)
        if artifact_id:
            graph[sid]["derived_artifacts"].append(
                {
                    "artifact_id": artifact_id,
                    "provenance_status": row.get("status", ""),
                    "row_hash": stable_hash_json(row),
                }
            )

    for row in quarantine_rows:
        sid = source_id(row)
        if sid not in graph:
            # Source was quarantined before/instead of ingestion (never reached ingestion manifest).
            # Seed a graph node so rollback replay can track its quarantine event.
            graph[sid] = {
                "source_id": sid,
                "custody_path": "",
                "integrity_reference": "",
                "derived_artifacts": [],
                "quarantine_events": [],
                "rollback_actions": [],
            }
        graph[sid]["quarantine_events"].append(
            {
                "quarantine_status": row.get("status", ""),
                "reason": row.get("reason", ""),
                "row_hash": stable_hash_json(row),
            }
        )

    for row in rollback_rows:
        sid = source_id(row)
        if sid not in graph:
            fail(f"rollback references unknown source_id={sid}")
        graph[sid]["rollback_actions"].append(
            {
                "rollback_action": row.get("rollback_action", ""),
                "rollback_scope": row.get("rollback_scope", ""),
                "status": row.get("status", ""),
                "row_hash": stable_hash_json(row),
            }
        )

    for sid, node in graph.items():
        node["derived_artifacts"] = sorted(node["derived_artifacts"], key=lambda x: x["artifact_id"])
        node["quarantine_events"] = sorted(node["quarantine_events"], key=lambda x: x["row_hash"])
        node["rollback_actions"] = sorted(node["rollback_actions"], key=lambda x: x["row_hash"])

    return dict(sorted(graph.items()))


def simulate_unwind(graph: dict) -> dict:
    replay_nodes = []

    for sid, node in graph.items():
        derived_count = len(node["derived_artifacts"])
        rollback_count = len(node["rollback_actions"])

        # A source with no derived artifacts (e.g. quarantine-only, never ingested)
        # has nothing to roll back — it is trivially reversible.
        if derived_count == 0:
            reversible = True
        else:
            reversible = rollback_count >= 1
        closure_status = "CLOSED" if reversible else "OPEN"

        replay_nodes.append(
            {
                "source_id": sid,
                "derived_artifact_count": derived_count,
                "rollback_action_count": rollback_count,
                "quarantine_event_count": len(node["quarantine_events"]),
                "simulated_removed_artifacts": [
                    item["artifact_id"] for item in node["derived_artifacts"]
                ],
                "reversible": reversible,
                "closure_status": closure_status,
            }
        )

    replay_nodes = sorted(replay_nodes, key=lambda x: x["source_id"])
    open_nodes = [n["source_id"] for n in replay_nodes if n["closure_status"] != "CLOSED"]

    return {
        "replay_nodes": replay_nodes,
        "open_nodes": open_nodes,
        "reversible_provenance_closure": not open_nodes,
    }


def main() -> int:
    ingestion_rows = read_csv(INGESTION_MANIFEST)
    provenance_rows = read_csv(PROVENANCE_MANIFEST)
    quarantine_rows = read_csv(QUARANTINE_MANIFEST)
    rollback_rows = read_csv(ROLLBACK_MANIFEST)

    graph = build_lineage_graph(
        ingestion_rows=ingestion_rows,
        provenance_rows=provenance_rows,
        quarantine_rows=quarantine_rows,
        rollback_rows=rollback_rows,
    )
    replay = simulate_unwind(graph)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result": "PASS" if replay["reversible_provenance_closure"] else "FAIL",
        "canonical_inputs": {
            "ingestion_manifest": str(INGESTION_MANIFEST.relative_to(GOV)),
            "provenance_manifest": str(PROVENANCE_MANIFEST.relative_to(GOV)),
            "quarantine_manifest": str(QUARANTINE_MANIFEST.relative_to(GOV)),
        },
        "runtime_inputs": {
            "rollback_manifest": str(ROLLBACK_MANIFEST.relative_to(GOV)),
        },
        "source_count": len(graph),
        "lineage_graph_hash": stable_hash_json(graph),
        "replay_hash": stable_hash_json(replay),
        "replay": replay,
    }

    write_json(REPLAY_GRAPH, {"lineage_graph": graph, "lineage_graph_hash": report["lineage_graph_hash"]})
    write_json(REPLAY_REPORT, report)

    print(f"ROLLBACK REPLAY {report['result']}")
    print(f"sources={report['source_count']}")
    print(f"lineage_graph_hash={report['lineage_graph_hash']}")
    print(f"replay_hash={report['replay_hash']}")

    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
