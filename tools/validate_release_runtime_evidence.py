"""Verify exact-source runtime proof; this never grants release authorization."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def read_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def report_properties(element):
    properties = {}
    for item in element.findall("./properties/property"):
        name, value = item.get("name"), item.get("value")
        if not name or value is None or name in properties:
            raise ValueError("JUnit properties must have unique names and explicit values")
        properties[name] = value
    return properties


def validate(path: Path, sha: str, environment: str, gate: str,
             keys: list[str], criteria: list[str], now=None) -> dict:
    errors = []
    now = now or datetime.now(timezone.utc)
    records = []
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Expected source SHA must be a complete Git identity")
        if environment not in {"sandbox", "staging", "production"}:
            raise ValueError("An explicit sandbox, staging, or production evidence environment is required")
        if not keys or len(keys) != len(set(keys)) or not criteria or len(criteria) != len(set(criteria)):
            raise ValueError("Required control keys and criteria must be nonempty and unique")
        payload = read_json(path)
        if payload.get("schema_version") != "1.0":
            raise ValueError("Unsupported runtime evidence schema")
        for field in ("source_sha", "backend_sha", "frontend_sha"):
            if payload.get(field) != sha:
                raise ValueError(f"{field} does not match the evaluated source")
        if payload.get("environment") != environment:
            raise ValueError("Runtime evidence targets a different environment")
        for field in ("runtime_id", "run_reference", "operator_reference"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                raise ValueError(f"Missing {field}")
        started = datetime.fromisoformat(payload["started_at"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(payload["completed_at"].replace("Z", "+00:00"))
        if started.tzinfo is None or completed.tzinfo is None or not now - timedelta(days=1) <= started <= completed <= now:
            raise ValueError("Runtime evidence must be completed, timezone-aware, and no more than 24 hours old")
        group = payload["gates"][gate]
        report = Path(group["junit_path"])
        if report.is_absolute() or ".." in report.parts:
            raise ValueError("Runtime report path must stay inside its evidence packet")
        report = (path.parent / report).resolve()
        if not report.is_relative_to(path.parent.resolve()):
            raise ValueError("Runtime report escapes its evidence packet")
        content = report.read_bytes()
        if len(content) > 16 * 1024 * 1024 or not content:
            raise ValueError("Runtime report is empty or oversized")
        if hashlib.sha256(content).hexdigest() != group.get("junit_sha256"):
            raise ValueError("Runtime report digest mismatch")
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("XML declarations are not allowed in runtime reports")
        root = ET.fromstring(content)
        if root.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Expected a JUnit testsuite report")
        properties = report_properties(root)
        for field in ("source_sha", "backend_sha", "frontend_sha", "environment", "runtime_id", "run_reference"):
            if properties.get(field) != payload[field]:
                raise ValueError(f"JUnit {field} does not match the evidence packet")
        cases = {}
        for case in root.iter("testcase"):
            identity = (case.get("classname"), case.get("name"))
            if identity in cases or not all(identity):
                raise ValueError("JUnit testcase identities must be present and unique")
            cases[identity] = case
            if any(case.find(tag) is not None for tag in ("failure", "error", "skipped")):
                raise ValueError("Runtime report contains failed, errored, or skipped proof")
        if not cases:
            raise ValueError("Runtime report contains no testcases")
        for suite in root.iter():
            if suite.tag not in {"testsuite", "testsuites"}:
                continue
            for field in ("failures", "errors", "skipped", "disabled"):
                if int(suite.get(field, "0")) != 0:
                    raise ValueError("Runtime report declares non-passing proof")
        records = group["records"]
        if not isinstance(records, list) or len(records) != len(keys):
            raise ValueError("Runtime proof does not cover every required control")
        by_key = {}
        used = set()
        for record in records:
            key = record["key"]
            if key in by_key or key not in keys:
                raise ValueError("Runtime control keys are duplicated or unexpected")
            by_key[key] = record
            proofs = record["proofs"]
            if set(proofs) != set(criteria):
                raise ValueError(f"{key}: missing or unexpected proof criteria")
            for criterion, identity in proofs.items():
                if not isinstance(identity, list) or len(identity) != 2 or tuple(identity) not in cases:
                    raise ValueError(f"{key}/{criterion}: executed testcase not found")
                if tuple(identity) in used:
                    raise ValueError("An executed testcase cannot substitute for multiple required proofs")
                used.add(tuple(identity))
            if gate == "performance":
                measured, targets = record["measured"], record["accepted_targets"]
                if not isinstance(record.get("target_approval_reference"), str) or not record["target_approval_reference"].strip():
                    raise ValueError(f"{key}: accepted targets require an approval reference")
                for field in ("users", "p95_ms", "error_rate"):
                    for values in (measured, targets):
                        value = values[field]
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                            raise ValueError(f"{key}: invalid numeric performance evidence")
                if targets["users"] <= 0 or targets["p95_ms"] <= 0 or targets["error_rate"] > 1 or measured["error_rate"] > 1:
                    raise ValueError(f"{key}: invalid accepted performance targets")
                if measured["users"] < targets["users"] or measured["p95_ms"] > targets["p95_ms"] or measured["error_rate"] > targets["error_rate"]:
                    raise ValueError(f"{key}: measured performance misses accepted targets")
                case = cases[tuple(proofs["load_test"])]
                measurements = report_properties(case)
                if any(float(measurements[field]) != measured[field] for field in ("users", "p95_ms", "error_rate")):
                    raise ValueError(f"{key}: performance measurements disagree with the executed report")
        if set(by_key) != set(keys):
            raise ValueError("Required runtime control coverage is incomplete")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
        errors.append(str(exc))
    return {"pass": not errors, "source_sha": sha, "environment": environment,
            "gate": gate, "errors": errors, "records": records if not errors else [],
            "authorization": "Evidence validation only; release authorization remains separate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--keys", required=True)
    parser.add_argument("--criteria", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = validate(args.manifest, args.sha, args.environment, args.gate,
                      args.keys.split(","), args.criteria.split(","))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
