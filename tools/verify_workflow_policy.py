#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
JOB_RE = re.compile(r"^\s{2}([A-Za-z0-9_-]+):\s*$", re.MULTILINE)
RUNS_ON_RE = re.compile(r"^\s{4}runs-on:\s*.+$", re.MULTILINE)
TIMEOUT_RE = re.compile(r"^\s{4}timeout-minutes:\s*\d+\s*$", re.MULTILINE)
CONT_ERR_RE = re.compile(r"^\s*continue-on-error:\s*true\s*$", re.MULTILINE | re.IGNORECASE)
MOJIBAKE_RE = re.compile(r"[âΓœ†œ©]")
NAME_RE = re.compile(r"(?m)^name:\s*(.+?)\s*$")
GROUP_RE = re.compile(r"(?m)^\s{2}group:\s*(.+?)\s*$")

CANONICAL_WORKFLOW_FILES = {
    "accounting-verification.yml",
    "azure-classroom-preflight.yml",
    "azure-drift-watchdog.yml",
    "backend-gate.yml",
    "ci.yml",
    "classroom-verification.yml",
    "codeql.yml",
    "content-operations-verification.yml",
    "contract-gate.yml",
    "crown-claims-guard.yml",
    "crown-release-authority-gates.yml",
    "dashboards-build-gate.yml",
    "demo-reset.yml",
    "dependency-audit.yml",
    "dependency-review.yml",
    "deploy-dashboard.yml",
    "deploy-dev.yml",
    "deploy-prod.yml",
    "dev-smoke.yml",
    "finance-final-hardening.yml",
    "isolated-postgres-restore-drill.yml",
    "license-audit.yml",
    "migration-lock-gate.yml",
    "ops-reset-dev.yml",
    "pr-preflight.yml",
    "prod-health-watch.yml",
    "prod-immutable-rollback-drill.yml",
    "prod-rollback-on-failure.yml",
    "production-certification-evidence.yml",
    "pytest-gate.yml",
    "recovery-control-drill.yml",
    "release-verify.yml",
    "repository-freshness.yml",
    "repository-policy.yml",
    "sbom-generation.yml",
    "schema-governance.yml",
    "schema-migration-stage.yml",
    "secret-scan.yml",
    "secrets-control-drill.yml",
    "stale-branches.yml",
    "tenant-isolation-gate.yml",
    "tests.yml",
    "ui-proof-gate.yml",
    "wizard-e2e-evidence-gate.yml",
    "workflow-permissions-audit.yml",
}


def is_pinned_uses(ref: str) -> bool:
    if ref.startswith("./") or ref.startswith("docker://"):
        return True
    if "@" not in ref:
        return False
    action, version = ref.split("@", 1)
    if action.startswith("./"):
        return True
    return bool(re.fullmatch(r"[0-9a-f]{40}", version))


def _check_dispatch_input_descriptions(text: str, rel: pathlib.Path) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()

    in_dispatch = False
    in_inputs = False
    current_input: str | None = None
    has_description = False

    for raw in lines:
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        if line == "workflow_dispatch:":
            in_dispatch = True
            in_inputs = False
            current_input = None
            has_description = False
            continue

        if in_dispatch and indent <= 1 and line.endswith(":") and line != "workflow_dispatch:":
            if current_input and not has_description:
                errors.append(f"{rel}: workflow_dispatch input '{current_input}' missing description")
            in_dispatch = False
            in_inputs = False
            current_input = None
            has_description = False

        if not in_dispatch:
            continue

        if line == "inputs:" and indent >= 4:
            in_inputs = True
            continue

        if not in_inputs:
            continue

        if indent <= 3:
            if current_input and not has_description:
                errors.append(f"{rel}: workflow_dispatch input '{current_input}' missing description")
            in_inputs = False
            current_input = None
            has_description = False
            continue

        input_match = re.match(r"^([A-Za-z0-9_-]+):\s*$", line)
        if indent >= 6 and input_match:
            if current_input and not has_description:
                errors.append(f"{rel}: workflow_dispatch input '{current_input}' missing description")
            current_input = input_match.group(1)
            has_description = False
            continue

        if current_input and line.startswith("description:"):
            has_description = True

    if current_input and not has_description:
        errors.append(f"{rel}: workflow_dispatch input '{current_input}' missing description")

    return errors


def _check_curl_safety(text: str, rel: pathlib.Path) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "curl " not in line:
            i += 1
            continue

        start_idx = i + 1
        cmd_parts = [line.strip()]
        while cmd_parts[-1].endswith("\\") and i + 1 < len(lines):
            i += 1
            cmd_parts.append(lines[i].strip())

        cmd = " ".join(cmd_parts)
        if cmd.strip().startswith("#"):
            i += 1
            continue

        explicit_status_probe = "%{http_code}" in cmd or "-w" in cmd
        if (
            "-f" not in cmd
            and "--fail" not in cmd
            and "-fsS" not in cmd
            and not explicit_status_probe
        ):
            errors.append(f"{rel}:{start_idx}: curl command missing fail-fast flag (-f/--fail)")
        if "--max-time" not in cmd and "--connect-timeout" not in cmd:
            errors.append(f"{rel}:{start_idx}: curl command missing timeout guard")

        i += 1
    return errors


def check_file(path: pathlib.Path) -> tuple[list[str], str | None, str | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(ROOT)
    errors: list[str] = []
    name = None
    group = None

    name_match = NAME_RE.search(text)
    if name_match:
        name = name_match.group(1).strip()

    group_match = GROUP_RE.search(text)
    if group_match:
        group = group_match.group(1).strip().strip('"').strip("'")

    if not re.search(r"(?m)^permissions:\s*$", text):
        errors.append(f"{rel}: missing top-level permissions block")

    if not re.search(r"(?m)^concurrency:\s*$", text):
        errors.append(f"{rel}: missing top-level concurrency block")

    jobs_match = re.search(r"(?ms)^jobs:\s*$([\s\S]+)$", text)
    if jobs_match:
        jobs_block = jobs_match.group(1)
        job_matches = list(JOB_RE.finditer(jobs_block))
        runner_jobs = 0
        runner_timeouts = 0
        for index, job_match in enumerate(job_matches):
            next_start = (
                job_matches[index + 1].start()
                if index + 1 < len(job_matches)
                else len(jobs_block)
            )
            job_block = jobs_block[job_match.end() : next_start]
            if RUNS_ON_RE.search(job_block):
                runner_jobs += 1
                if TIMEOUT_RE.search(job_block):
                    runner_timeouts += 1
        if runner_jobs and runner_timeouts < runner_jobs:
            errors.append(
                f"{rel}: missing timeout-minutes on one or more runner jobs "
                f"({runner_timeouts}/{runner_jobs})"
            )

    if CONT_ERR_RE.search(text):
        errors.append(f"{rel}: contains continue-on-error: true")

    if MOJIBAKE_RE.search(text):
        errors.append(f"{rel}: contains mojibake/non-clean text sequences")

    if "workflow_run:" in text:
        if "head_repository.full_name" not in text:
            errors.append(f"{rel}: workflow_run missing source repository trust guard")
        if "head_sha" not in text:
            errors.append(f"{rel}: workflow_run missing head_sha validation context")

    if "workflow_dispatch:" in text and "inputs:" in text:
        errors.extend(_check_dispatch_input_descriptions(text, rel))

    errors.extend(_check_curl_safety(text, rel))

    if "deploy-prod" in path.name and re.search(r"(?m)^\s{2}pull_request:\s*$", text):
        errors.append(f"{rel}: production deploy workflow must not trigger on pull_request")

    for match in USES_RE.findall(text):
        if not is_pinned_uses(match):
            errors.append(f"{rel}: unpinned uses reference '{match}'")

    return errors, name, group


def main() -> int:
    targets = [pathlib.Path(p).resolve() for p in sys.argv[1:]]
    all_errors: list[str] = []

    active_workflows = {path.name for path in WORKFLOWS.glob("*.yml")}
    unexpected = sorted(active_workflows - CANONICAL_WORKFLOW_FILES)
    missing = sorted(CANONICAL_WORKFLOW_FILES - active_workflows)
    if unexpected:
        all_errors.append(
            "unexpected top-level workflows outside the canonical inventory: "
            + ", ".join(unexpected)
        )
    if missing:
        all_errors.append(
            "canonical workflow inventory is missing expected files: "
            + ", ".join(missing)
        )
    if len(active_workflows) != len(CANONICAL_WORKFLOW_FILES):
        all_errors.append(
            f"workflow count {len(active_workflows)} does not match canonical count "
            f"{len(CANONICAL_WORKFLOW_FILES)}"
        )

    names: dict[str, pathlib.Path] = {}
    groups: dict[str, pathlib.Path] = {}
    files = targets if targets else sorted(WORKFLOWS.glob("*.yml"))
    for wf in files:
        if not wf.exists() or wf.suffix.lower() != ".yml":
            continue
        if wf.parent != WORKFLOWS:
            continue
        errors, name, group = check_file(wf)
        all_errors.extend(errors)
        rel = wf.relative_to(ROOT)

        if name:
            if name in names and names[name] != wf:
                all_errors.append(
                    f"{rel}: duplicate workflow name '{name}' also used by {names[name].relative_to(ROOT)}"
                )
            else:
                names[name] = wf

        if group:
            if group in groups and groups[group] != wf:
                all_errors.append(
                    f"{rel}: duplicate top-level concurrency group '{group}' also used by {groups[group].relative_to(ROOT)}"
                )
            else:
                groups[group] = wf

    if all_errors:
        print("Workflow policy violations detected:")
        for err in all_errors:
            print(f" - {err}")
        return 1

    print("Workflow policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
