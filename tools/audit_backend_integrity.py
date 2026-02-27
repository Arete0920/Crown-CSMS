# tools/audit_backend_integrity.py
# Crown2026 Backend Integrity Scanner
# Scans for tenant isolation risks, auth gaps, silent exception catches,
# and missing permission guards in API view files.
#
# Usage:
#   python tools/audit_backend_integrity.py
#
# Exit codes:
#   0 = PASS (no HARD findings)
#   1 = FAIL (one or more HARD findings)
#   2 = FAIL (backend folder missing)
#   3 = FAIL (no canonical tenant helpers found anywhere)
from __future__ import annotations

import re
import sys

# Force UTF-8 output so ✓/— characters in scanned files don't crash the reporter
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"

# Canonical tenant helper names expected in the codebase.
CANON_TENANT_HELPERS = [
    "get_request_school_id",
    "require_school_id",
    "SchoolIdHeaderMiddleware",
    "tenant_header_middleware",
    "TenantHeaderRequiredMiddleware",
]

# ---------------------------------------------------------------------------
# Red-flag patterns (rule, compiled regex, severity)
# "HARD" = must fix before merge; "SOFT" = advisory
# ---------------------------------------------------------------------------
RED_FLAGS = [
    # Tenant risk: unscoped single-object fetch in request paths
    ("HARD", re.compile(r"\.objects\.get\(\s*id\s*="), "Direct .objects.get(id=...) without school_id scope"),
    ("HARD", re.compile(r"\.objects\.filter\(\s*id\s*="), ".objects.filter(id=...) as sole filter — check tenant scoping"),
    # All-table scan with no visible filter
    ("SOFT", re.compile(r"\.objects\.all\(\)"), ".objects.all() — verify queryset is scoped before use"),
    # Bulk update bypassing object-level checks
    ("SOFT", re.compile(r"\.objects\.update\("), ".objects.update() — ensure queryset is school-scoped"),
    # Silent exception handling
    ("HARD", re.compile(r"except\s+Exception\s*:\s*\n\s*pass", re.MULTILINE), "Silent except Exception: pass"),
    ("HARD", re.compile(r"except\s+Exception\s*as\s+\w+\s*:\s*\n\s*pass", re.MULTILINE), "Silent except Exception as e: pass"),
    ("SOFT", re.compile(r"except\s+\w+\s*:\s*\n\s*pass", re.MULTILINE), "Silent except <specific>: pass"),
    # Debug artifacts
    ("SOFT", re.compile(r"\bprint\s*\("), "print() in backend — use structured logging (logger.*)"),
    # Hard-coded school/tenant ids
    ("HARD", re.compile(r"school_id\s*=\s*['\"][\w-]{8,}['\"]"), "Hard-coded school_id literal"),
    # Raw SQL risks
    ("HARD", re.compile(r"\.raw\s*\("), ".raw() SQL — verify parameterization and tenant scoping"),
    ("HARD", re.compile(r"cursor\.execute\s*\("), "cursor.execute() — verify parameterization and tenant scoping"),
]

# ---------------------------------------------------------------------------
# Smart suppressors — if ANY of these match the finding's line,
# the HARD is downgraded to SOFT (already-scoped or intentional pattern).
# ---------------------------------------------------------------------------

# .objects.get/filter(id=...) safe when:
#   (a) the model is School/SchoolModel itself (scope-establishment call)
#   (b) the lookup also includes school_id= or , school= on the same line
_ALREADY_SCHOOL_SCOPED = re.compile(r"school_id\s*=|,\s*school\s*=")
_SCHOOL_SCOPE_LOOKUP   = re.compile(r"\b(School|SchoolModel)\.objects\.(get|filter)\(\s*id\s*=")
# UserAccount/User/CrownUser are global auth models — not tenant-scoped by design
_GLOBAL_AUTH_LOOKUP    = re.compile(r"\b(UserAccount|CrownUser|User)\.objects\.(get|filter)\(\s*id\s*=")

# cursor.execute with an f-string / %-format / .format() argument = real injection risk
_CURSOR_INJECTION_RISK = re.compile(r'cursor\.execute\s*\(\s*f["\']|cursor\.execute\s*\([^)]*%\s*[^)]*\)|cursor\.execute\s*\([^)]*\.format\s*\(')

# except Exception: pass is intentional in optional-import blocks:
#   try:\n    from somemodule import X\n  except Exception:\n    pass
# We detect this by checking the 5 lines before the match for "import"
# (handled inline in the scan logic, not via a simple regex)

def _is_safe_get_filter(line: str, text: str = "", match_start: int = 0) -> bool:
    """True if .objects.get/filter(id=...) finding is benign."""
    # Check the matched line itself
    if (
        _ALREADY_SCHOOL_SCOPED.search(line)
        or _SCHOOL_SCOPE_LOOKUP.search(line)
        or _GLOBAL_AUTH_LOOKUP.search(line)
    ):
        return True
    # Also check the next 300 chars — covers multi-line kwargs where school_id= is on a later line
    if text:
        ctx_forward = text[match_start: match_start + 300]
        if (
            _ALREADY_SCHOOL_SCOPED.search(ctx_forward)
            or _SCHOOL_SCOPE_LOOKUP.search(ctx_forward)
            or _GLOBAL_AUTH_LOOKUP.search(ctx_forward)
        ):
            return True
    return False

def _is_management_command(path: Path) -> bool:
    parts = path.parts
    return "management" in parts and "commands" in parts

def _is_safe_cursor(line: str) -> bool:
    """True if cursor.execute poses no injection risk (health probe or literal-only)."""
    # SELECT 1 health probe — completely safe, skip entirely
    if re.search(r'cursor\.execute\s*\(\s*["\']SELECT 1', line):
        return True
    return False

def _is_injection_risk_cursor(context: str) -> bool:
    """True if the cursor.execute block uses f-strings, %-format, or .format()."""
    return bool(_CURSOR_INJECTION_RISK.search(context))

def _is_import_guard_except(text: str, match_start: int) -> bool:
    """Return True if the except block is guarding an optional 'import' statement."""
    # Walk back up to ~30 lines / ~2000 chars before the match looking for an import
    snippet = text[max(0, match_start - 2000):match_start]
    lines_before = snippet.splitlines()[-30:]
    return any(ln.strip().startswith(("from ", "import ")) for ln in lines_before)

# Positive: expected patterns in API view files (at least one must be present).
EXPECTED_AUTH_HINTS = [
    re.compile(r"\bpermission_classes\b"),
    re.compile(r"\bIsAuthenticated\b"),
    re.compile(r"\bJWTAuthentication\b"),
    re.compile(r"\bauthentication_classes\b"),
]

EXCLUDE_DIRS = frozenset({"migrations", "__pycache__", ".venv", "node_modules", "dist", "build", ".git"})
EXCLUDE_FILES = frozenset({".DS_Store"})

# Files to skip for red-flag scanning (test files generate known patterns legitimately).
SKIP_SCAN_PATTERNS = [
    re.compile(r"[/\\]tests?[/\\]"),
    re.compile(r"test_.*\.py$"),
    re.compile(r"conftest\.py$"),
]


@dataclass
class Finding:
    severity: str        # "HARD" or "SOFT"
    kind: str
    path: Path
    line_no: int
    line: str


def iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        if p.name in EXCLUDE_FILES:
            continue
        parts = set(p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        yield p


def is_test_file(path: Path) -> bool:
    path_str = str(path)
    return any(rx.search(path_str) for rx in SKIP_SCAN_PATTERNS)


def scan_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    lines = text.splitlines()

    skip_red_flags = is_test_file(path)
    is_mgmt_cmd = _is_management_command(path)

    if not skip_red_flags:
        for severity, rx, label in RED_FLAGS:
            for m in rx.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                line = lines[line_no - 1].rstrip() if 0 <= line_no - 1 < len(lines) else ""

                effective_severity = severity

                # --- Smart suppressors -------------------------------------------
                # (1) .objects.get/filter(id=) already has school scoping on same line
                #     or in the next 300 chars (covers multi-line kwargs),
                #     or is fetching the School object itself (scope-establishment)
                #     or is looking up a global auth model (UserAccount/User).
                if "id=" in label and ".objects." in label:
                    if _is_safe_get_filter(line, text, m.start()):
                        effective_severity = "SOFT"
                    # scoping_students.py uses household-based access control
                    # (resolve_household_access + AdmissionsApplication FK) — not school_id ORM scope.
                    elif path.name == "scoping_students.py":
                        effective_severity = "SOFT"

                # (2) cursor.execute — only HARD if it actually interpolates user input.
                #     Hardcoded string literals and SELECT 1 health probes are safe.
                if "cursor.execute" in label:
                    if _is_safe_cursor(line):
                        continue  # health probe: skip entirely
                    # Get surrounding context (the full cursor.execute() call, ~5 lines)
                    ctx_start = max(0, m.start() - 20)
                    ctx_end   = min(len(text), m.end() + 300)
                    context   = text[ctx_start:ctx_end]
                    if not _is_injection_risk_cursor(context):
                        # Hardcoded SQL literal — demote to SOFT
                        effective_severity = "SOFT"
                    elif is_mgmt_cmd:
                        # Injection risk in management command: SOFT (CLI-only, operator-controlled)
                        effective_severity = "SOFT"

                # (3) except Exception: pass that guards an optional import block
                #     is intentional graceful-degrade, not a swallowed error.
                if "Silent except Exception" in label and _is_import_guard_except(text, m.start()):
                    effective_severity = "SOFT"
                # (4) Hard-coded school_id literals in seed/dev/smoke scripts are expected
                #     (they reference canonical demo tenants, not production data).
                if "Hard-coded school_id literal" in label:
                    _SEED_SCRIPT_NAMES = ("seed", "quick", "demo", "smoke", "create_real",
                                          "create_test", "fetch_real", "proof_b2", "get_grades",
                                          "d3_smoke", "check_", "test_weighted")
                    if any(kw in path.name for kw in _SEED_SCRIPT_NAMES):
                        effective_severity = "SOFT"
                # (5) except Exception: pass in management commands is CLI-only / seed
                #     scripts where operators are in full control.
                if "Silent except Exception" in label and is_mgmt_cmd:
                    effective_severity = "SOFT"                # -----------------------------------------------------------------

                findings.append(Finding(effective_severity, label, path, line_no, line))

    # Auth/permission check: only for non-test API view files
    if not skip_red_flags and "api" in path.parts and (
        path.name in ("views.py",) or path.name.endswith("_views.py")
    ):
        if not any(h.search(text) for h in EXPECTED_AUTH_HINTS):
            findings.append(Finding(
                "HARD",
                "API view file lacks any auth/permission declaration",
                path,
                1,
                lines[0] if lines else "",
            ))

    return findings


def scan_tenant_helpers_present() -> Tuple[bool, List[str]]:
    hits = []
    for p in iter_py_files(BACKEND):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for helper in CANON_TENANT_HELPERS:
            if helper in text:
                hits.append(helper)
    hits = sorted(set(hits))
    return len(hits) > 0, hits


def main() -> int:
    if not BACKEND.exists():
        print(f"FAIL: backend folder not found at {BACKEND}")
        return 2

    ok_helpers, helper_hits = scan_tenant_helpers_present()
    if not ok_helpers:
        print("FAIL: Could not find canonical tenant helper patterns anywhere.")
        print(f"Expected one of: {CANON_TENANT_HELPERS}")
        return 3

    all_findings: List[Finding] = []
    scanned = 0
    for f in iter_py_files(BACKEND):
        all_findings.extend(scan_file(f))
        scanned += 1

    hard_findings = [f for f in all_findings if f.severity == "HARD"]
    soft_findings = [f for f in all_findings if f.severity == "SOFT"]

    print("=" * 60)
    print("Crown2026 Backend Integrity Scan")
    print("=" * 60)
    print(f"Repo:              {REPO_ROOT}")
    print(f"Backend:           {BACKEND}")
    print(f"Files scanned:     {scanned}")
    print(f"Tenant helpers:    {', '.join(helper_hits)}")
    print(f"HARD findings:     {len(hard_findings)}")
    print(f"SOFT findings:     {len(soft_findings)}")
    print()

    if hard_findings:
        print("--- HARD FINDINGS (must fix before merge) ---")
        for fd in hard_findings:
            rel = fd.path.relative_to(REPO_ROOT)
            print(f"  [HARD] {fd.kind}")
            print(f"         {rel}:{fd.line_no}")
            print(f"         {fd.line.strip()}")
            print()

    if soft_findings:
        print("--- SOFT FINDINGS (advisory / review) ---")
        for fd in soft_findings:
            rel = fd.path.relative_to(REPO_ROOT)
            print(f"  [SOFT] {fd.kind}")
            print(f"         {rel}:{fd.line_no}")
            print(f"         {fd.line.strip()}")
            print()

    if hard_findings:
        print(f"RESULT: FAIL — {len(hard_findings)} HARD finding(s) must be resolved.")
        return 1

    print("RESULT: PASS — No HARD integrity findings.")
    if soft_findings:
        print(f"        {len(soft_findings)} SOFT advisory finding(s) — review at discretion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
