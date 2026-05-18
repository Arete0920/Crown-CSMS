#!/usr/bin/env python3
"""Generate deterministic audit evidence bundles for Crown2026.

Design rules implemented:
1. Deterministic ordering.
2. UTF-8 + LF output.
3. Runtime-only generation first (default).
4. Explicit promotion into canonical AUDIT_PACK.
5. No silent overwrite.
6. Timestamped evidence bundle manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from env_guard import validate_environment
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment


ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / "solomon_governance_c1"
RUNTIME_PACK_ROOT = SOL / "governance" / "c1" / "runtime" / "audit_pack"
CANONICAL_PACK = ROOT / "AUDIT_PACK"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
RULESET_MAIN_NAME = "ruleset_main.json"
MANIFEST_NAME = "99_BUNDLE_MANIFEST.json"
LATEST_BUNDLE_NAME = "LATEST_BUNDLE.txt"

REQUIRED_FILES = [
    "00_OVERVIEW.txt",
    "01_TREE.txt",
    "02_WORKFLOWS_INDEX.txt",
    "03_WORKFLOWS_TRIGGERS.txt",
    "04_JOB_LEVEL_IF.txt",
    "05_BRANCH_PROTECTION_MAIN.json",
    "06_BACKEND_URLS.txt",
    "07_MIGRATIONS.txt",
    "08_PY_DEPS.txt",
    "09_NODE_DEPS.txt",
    "10_SECRET_SCAN_FINDINGS.txt",
    "11_TRACKED_BINARIES.txt",
    "12_UNTRACKED_ARTIFACTS.txt",
    "13_HEALTH_PROBE.txt",
    "14_DEPLOY_PROD_RECENT.txt",
]

BINARY_EXT_RE = re.compile(r"\.(png|jpg|jpeg|gif|pdf|zip|exe|dll|so|dylib|jar|bin)$", re.IGNORECASE)
SECRET_PATTERNS = [
    ("AWS_ACCESS_KEY_ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    # Split the literal to avoid false positives in repository secret scanners.
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE" + r" KEY-----")),
    ("GENERIC_API_KEY", re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"][A-Za-z0-9._-]{16,}['\"]")),
]


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_bundle_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def list_workflow_files() -> list[Path]:
    if not WORKFLOWS_DIR.exists():
        return []
    files = list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
    return sorted(files, key=lambda p: p.name.lower())


def parse_workflow_triggers(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_on = False
    on_re = re.compile(r"^on\s*:\s*$")
    on_inline_re = re.compile(r"^on\s*:\s*.+$")
    top_key_re = re.compile(r"^[A-Za-z0-9_\-]+\s*:\s*")

    for idx, line in enumerate(lines, start=1):
        if not in_on:
            if on_re.match(line) or on_inline_re.match(line):
                out.append(f"{idx:4d}: {line}")
                if on_re.match(line):
                    in_on = True
        else:
            if top_key_re.match(line):
                break
            out.append(f"{idx:4d}: {line}")

    return "\n".join(out) if out else "(no trigger stanza detected)"


def parse_workflow_job_ifs(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[str] = []
    in_jobs = False
    current_job = ""

    for idx, line in enumerate(lines, start=1):
        if re.match(r"^jobs\s*:\s*$", line):
            in_jobs = True
            current_job = ""
            continue

        if in_jobs and re.match(r"^[A-Za-z0-9_\-]+\s*:\s*", line):
            break

        if in_jobs:
            job_match = re.match(r"^\s{2}([A-Za-z0-9_.\-]+)\s*:\s*$", line)
            if job_match:
                current_job = job_match.group(1)
                continue
            if_match = re.match(r"^\s{4}if\s*:\s*(.+)$", line)
            if if_match and current_job:
                entries.append(
                    f"{path.relative_to(ROOT).as_posix()}:{idx} "
                    f"job={current_job} if={if_match.group(1).strip()}"
                )

    return sorted(entries)


def find_backend_urls() -> list[str]:
    hits: set[str] = set()
    backend = ROOT / "backend"
    if not backend.exists():
        return []

    url_re = re.compile(r"['\"](/api/[^'\"]*|/health/?[^'\"]*|/[^'\"]*health[^'\"]*)['\"]")
    path_re = re.compile(r"\b(path|re_path)\s*\(\s*['\"]([^'\"]+)['\"]")

    for file_path in sorted(backend.rglob("*.py"), key=lambda p: p.as_posix()):
        rel = file_path.relative_to(ROOT).as_posix()
        for idx, line in enumerate(file_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for m in url_re.finditer(line):
                hits.add(f"{rel}:{idx} literal={m.group(1)}")
            pm = path_re.search(line)
            if pm:
                hits.add(f"{rel}:{idx} route={pm.group(2)}")

    return sorted(hits)


def find_migrations() -> list[str]:
    paths: set[str] = set()
    for base in [ROOT / "backend", ROOT / "src"]:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*"), key=lambda x: x.as_posix()):
            if p.is_file() and ("migrations" in p.parts or re.search(r"migration", p.name, re.IGNORECASE)):
                paths.add(p.relative_to(ROOT).as_posix())
    return sorted(paths)


def collect_python_deps() -> list[str]:
    out: list[str] = []
    req_files = [ROOT / "requirements.txt", ROOT / "backend" / "requirements.txt"]
    for req in req_files:
        if not req.exists():
            continue
        rel = req.relative_to(ROOT).as_posix()
        out.append(f"[{rel}]")
        for line in req.read_text(encoding="utf-8").splitlines():
            item = line.strip()
            if not item or item.startswith("#"):
                continue
            out.append(item)
        out.append("")
    return out


def collect_node_deps() -> list[str]:
    out: list[str] = []
    for pkg in sorted(ROOT.rglob("package.json"), key=lambda p: p.as_posix()):
        if ".git" in pkg.parts or "node_modules" in pkg.parts:
            continue
        rel = pkg.relative_to(ROOT).as_posix()
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except Exception:
            out.append(f"[{rel}] INVALID_JSON")
            out.append("")
            continue

        out.append(f"[{rel}]")
        for section in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
            deps = data.get(section) or {}
            if not deps:
                continue
            out.append(f"{section}:")
            for name in sorted(deps):
                out.append(f"  {name}={deps[name]}")
        out.append("")

    return out


def scan_secret_metadata(excluded_roots: list[Path]) -> list[str]:
    findings: set[str] = set()
    excluded = [p.resolve() for p in excluded_roots if p.exists()]

    for p in sorted(ROOT.rglob("*"), key=lambda x: x.as_posix()):
        if not p.is_file():
            continue
        if any(part in {".git", "node_modules"} for part in p.parts):
            continue
        if BINARY_EXT_RE.search(p.name):
            continue

        resolved = p.resolve()
        if any(str(resolved).startswith(str(ex)) for ex in excluded):
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel = p.relative_to(ROOT).as_posix()
        for idx, line in enumerate(text.splitlines(), start=1):
            for category, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.add(f"{rel}:{idx} category={category}")

    return sorted(findings)


def write_required_files(pack_dir: Path) -> None:
    rc_branch, branch_out, _ = run_cmd(["git", "branch", "--show-current"])
    rc_head, head_out, _ = run_cmd(["git", "rev-parse", "HEAD"])
    rc_status, status_out, _ = run_cmd(["git", "status", "--short", "--branch"])

    tracked_rc, tracked_out, tracked_err = run_cmd(["git", "ls-files"])
    tracked_files = sorted([x for x in tracked_out.splitlines() if x.strip()]) if tracked_rc == 0 else []
    workflows = list_workflow_files()

    overview_lines = [
        "Crown2026 Deterministic Audit Pack",
        f"root={ROOT.as_posix()}",
        f"git_branch={(branch_out.strip() if rc_branch == 0 else 'UNKNOWN')}",
        f"git_head={(head_out.strip() if rc_head == 0 else 'UNKNOWN')}",
        f"git_status_rc={rc_status}",
        "",
        "git_status_short_branch:",
        status_out.strip() if status_out.strip() else "(clean or unavailable)",
        "",
        f"workflow_count={len(workflows)}",
        f"tracked_file_count={len(tracked_files)}",
    ]
    write_text(pack_dir / "00_OVERVIEW.txt", "\n".join(overview_lines))

    tree_lines = ["Tracked files (git ls-files):"] + tracked_files
    if tracked_rc != 0:
        tree_lines = ["ERROR: git ls-files failed", tracked_err.strip()]
    write_text(pack_dir / "01_TREE.txt", "\n".join(tree_lines))

    wf_index = [p.relative_to(ROOT).as_posix() for p in workflows]
    write_text(pack_dir / "02_WORKFLOWS_INDEX.txt", "\n".join(wf_index) if wf_index else "(no workflow files found)")

    trigger_blocks: list[str] = []
    for wf in workflows:
        trigger_blocks.append(f"## {wf.relative_to(ROOT).as_posix()}")
        trigger_blocks.append(parse_workflow_triggers(wf))
        trigger_blocks.append("")
    trigger_text = "\n".join(trigger_blocks).rstrip() if trigger_blocks else "(no workflow trigger data)"
    write_text(pack_dir / "03_WORKFLOWS_TRIGGERS.txt", trigger_text)

    if_entries: list[str] = []
    for wf in workflows:
        if_entries.extend(parse_workflow_job_ifs(wf))
    write_text(pack_dir / "04_JOB_LEVEL_IF.txt", "\n".join(sorted(if_entries)) if if_entries else "(no job-level if conditions detected)")

    ruleset_main = ROOT / RULESET_MAIN_NAME
    if ruleset_main.exists():
        try:
            data = json.loads(ruleset_main.read_text(encoding="utf-8"))
            payload = {"source": RULESET_MAIN_NAME, "path": ruleset_main.relative_to(ROOT).as_posix(), "data": data}
        except Exception as exc:
            payload = {"source": RULESET_MAIN_NAME, "path": ruleset_main.relative_to(ROOT).as_posix(), "error": str(exc)}
    else:
        payload = {"source": "unavailable", "error": f"{RULESET_MAIN_NAME} not found in repository"}
    write_text(pack_dir / "05_BRANCH_PROTECTION_MAIN.json", json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))

    backend_urls = find_backend_urls()
    write_text(pack_dir / "06_BACKEND_URLS.txt", "\n".join(backend_urls) if backend_urls else "(no backend URL or route patterns found)")

    migrations = find_migrations()
    write_text(pack_dir / "07_MIGRATIONS.txt", "\n".join(migrations) if migrations else "(no migration files found)")

    py_deps = collect_python_deps()
    write_text(pack_dir / "08_PY_DEPS.txt", "\n".join(py_deps).rstrip() if py_deps else "(no requirements files found)")

    node_deps = collect_node_deps()
    write_text(pack_dir / "09_NODE_DEPS.txt", "\n".join(node_deps).rstrip() if node_deps else "(no package.json files found)")

    secret_findings = scan_secret_metadata(excluded_roots=[CANONICAL_PACK, RUNTIME_PACK_ROOT])
    secret_lines = ["Metadata only; secret values are never emitted."]
    secret_lines.extend(secret_findings if secret_findings else ["(no findings detected by local metadata scan)"])
    write_text(pack_dir / "10_SECRET_SCAN_FINDINGS.txt", "\n".join(secret_lines))

    tracked_binaries = [p for p in tracked_files if BINARY_EXT_RE.search(p)]
    write_text(pack_dir / "11_TRACKED_BINARIES.txt", "\n".join(tracked_binaries) if tracked_binaries else "(no tracked binary-like files)")

    rc_untracked, untracked_out, _ = run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    untracked_lines = sorted([x for x in untracked_out.splitlines() if x.strip()]) if rc_untracked == 0 else ["(failed to enumerate untracked files)"]
    write_text(pack_dir / "12_UNTRACKED_ARTIFACTS.txt", "\n".join(untracked_lines) if untracked_lines else "(no untracked files)")

    health_patterns = re.compile(r"health|/health|healthz|readiness|liveness", re.IGNORECASE)
    health_hits: list[str] = []
    for base in [ROOT / "solomon_governance_c1", ROOT / "backend", ROOT / "docs"]:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*"), key=lambda x: x.as_posix()):
            if not p.is_file():
                continue
            if any(part in {".git", "node_modules"} for part in p.parts):
                continue
            if BINARY_EXT_RE.search(p.name):
                continue
            resolved = p.resolve()
            if str(resolved).startswith(str(CANONICAL_PACK.resolve())):
                continue
            if str(resolved).startswith(str(RUNTIME_PACK_ROOT.resolve())):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for idx, line in enumerate(text.splitlines(), start=1):
                if health_patterns.search(line):
                    health_hits.append(f"{p.relative_to(ROOT).as_posix()}:{idx}: {line.strip()}")
    if not health_hits:
        health_hits = ["(no health/readiness/liveness references found)"]
    write_text(pack_dir / "13_HEALTH_PROBE.txt", "\n".join(health_hits))

    deploy_names = ["deploy-prod", "deploy_prod", "prod-health-watch", "prod-integrity-proof", "proof-ceremony-prod"]
    deploy_files = [p for p in workflows if any(name in p.name for name in deploy_names)]
    recent_blocks: list[str] = []
    for p in deploy_files:
        rel = p.relative_to(ROOT).as_posix()
        recent_blocks.append(f"## {rel}")
        rc_log, out_log, _ = run_cmd(["git", "log", "-n", "5", "--pretty=format:%h %ad %an %s", "--date=iso", "--", rel])
        if rc_log == 0 and out_log.strip():
            recent_blocks.append(out_log.strip())
        else:
            recent_blocks.append("(no commit history available)")
        recent_blocks.append("")
    if not recent_blocks:
        recent_blocks = ["(no deploy-prod workflow files discovered)"]
    write_text(pack_dir / "14_DEPLOY_PROD_RECENT.txt", "\n".join(recent_blocks).rstrip())


def write_bundle_manifest(bundle_dir: Path, bundle_id: str) -> None:
    file_hashes = {name: sha256_file(bundle_dir / name) for name in sorted(REQUIRED_FILES)}

    rc_branch, branch_out, _ = run_cmd(["git", "branch", "--show-current"])
    rc_head, head_out, _ = run_cmd(["git", "rev-parse", "HEAD"])

    manifest = {
        "bundle_id": bundle_id,
        "generated_at_utc": now_utc_iso(),
        "generator": "solomon_governance_c1/generate_audit_pack.py",
        "git_branch": branch_out.strip() if rc_branch == 0 else "UNKNOWN",
        "git_head": head_out.strip() if rc_head == 0 else "UNKNOWN",
        "required_files": sorted(REQUIRED_FILES),
        "file_sha256": file_hashes,
    }
    write_text(bundle_dir / MANIFEST_NAME, json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))


def validate_bundle(bundle_dir: Path) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (bundle_dir / name).exists()]
    if not (bundle_dir / MANIFEST_NAME).exists():
        missing.append(MANIFEST_NAME)
    return missing


def generate_runtime_bundle(bundle_id: str | None, force: bool) -> int:
    RUNTIME_PACK_ROOT.mkdir(parents=True, exist_ok=True)
    resolved_bundle_id = bundle_id or timestamp_bundle_id()
    bundle_dir = RUNTIME_PACK_ROOT / resolved_bundle_id

    if bundle_dir.exists():
        if not force:
            print(f"FAILED: bundle already exists: {bundle_dir}")
            print("Use --force to overwrite explicitly.")
            return 1
        shutil.rmtree(bundle_dir)

    bundle_dir.mkdir(parents=True, exist_ok=True)
    write_required_files(bundle_dir)
    write_bundle_manifest(bundle_dir, resolved_bundle_id)
    write_text(RUNTIME_PACK_ROOT / LATEST_BUNDLE_NAME, resolved_bundle_id)

    missing = validate_bundle(bundle_dir)
    if missing:
        print("FAILED: bundle validation missing files")
        for name in missing:
            print(f"- {name}")
        return 1

    print("RUNTIME_AUDIT_BUNDLE_GENERATED")
    print(f"bundle_id={resolved_bundle_id}")
    print(f"bundle_path={bundle_dir.as_posix()}")
    print("promote_command=")
    print(f"  python {SOL.as_posix()}/generate_audit_pack.py promote --bundle {bundle_dir.as_posix()}")
    return 0


def promote_bundle(bundle: Path, force: bool) -> int:
    bundle_dir = bundle.resolve()
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        print(f"FAILED: bundle not found: {bundle_dir}")
        return 1

    missing = validate_bundle(bundle_dir)
    if missing:
        print("FAILED: bundle validation missing files")
        for name in missing:
            print(f"- {name}")
        return 1

    if CANONICAL_PACK.exists():
        if not force:
            print(f"FAILED: canonical pack exists: {CANONICAL_PACK}")
            print("Use --force to overwrite explicitly after governance approval.")
            return 1
        shutil.rmtree(CANONICAL_PACK)

    CANONICAL_PACK.mkdir(parents=True, exist_ok=True)
    for name in sorted(REQUIRED_FILES + [MANIFEST_NAME]):
        shutil.copy2(bundle_dir / name, CANONICAL_PACK / name)

    print("AUDIT_PACK_PROMOTED")
    print(f"source_bundle={bundle_dir.as_posix()}")
    print(f"canonical_path={CANONICAL_PACK.as_posix()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and promote deterministic audit evidence bundles")
    sub = parser.add_subparsers(dest="command", required=False)

    gen = sub.add_parser("generate", help="Generate runtime audit bundle")
    gen.add_argument("--bundle-id", default=None, help="Optional deterministic bundle id")
    gen.add_argument("--force", action="store_true", help="Overwrite existing runtime bundle path")

    promote = sub.add_parser("promote", help="Promote runtime bundle to canonical AUDIT_PACK")
    promote.add_argument("--bundle", required=True, help="Path to runtime bundle directory")
    promote.add_argument("--force", action="store_true", help="Overwrite existing canonical AUDIT_PACK")

    return parser


def main() -> int:
    validate_environment()
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "generate"
    if command == "generate":
        return generate_runtime_bundle(
            bundle_id=getattr(args, "bundle_id", None),
            force=getattr(args, "force", False),
        )
    if command == "promote":
        return promote_bundle(bundle=Path(args.bundle), force=getattr(args, "force", False))

    print(f"FAILED: unknown command {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
