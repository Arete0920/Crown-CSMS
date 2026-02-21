#!/usr/bin/env python3
"""
check_ui_shell.py — Crown UI Shell Gate

Enforces that plain-React routed pages use CrownLayout instead of
raw padding wrappers, root <h1> headings, or bespoke fontFamily shells.

Rules (applied only to files NOT importing CrownLayout):
  [font-shell]   fontFamily system-ui in file (outer wrapper smell)
  [root-h1]      <h1> element present without CrownLayout
  [raw-wrapper]  <div style={{ padding: ... }} as outer wrapper

MUI pages and pages with non-standard styling paradigms are skipped via SKIP.
"""
import re
import sys
from pathlib import Path

PAGES_DIR = Path("frontend/dashboards/src/pages")

# Pages intentionally excluded from this gate
SKIP = {
    "LoginPage.jsx",                # auth surface, standalone by design
    "TeacherDashboard.jsx",         # MUI
    "ClassroomsDashboard.jsx",      # MUI
    "AcademicsTeacherGrading.jsx",  # MUI
    "AcademicsStudentWork.jsx",     # MUI
    "AcademicsParentSnapshot.jsx",  # MUI
    "ParentStudent360Page.jsx",     # MUI
    "ServiceHoursPage.jsx",         # Tailwind/shadcn paradigm (separate concern)
}

CROWN_IMPORT_RE = re.compile(r"import\s+CrownLayout\b")
H1_RE = re.compile(r"<h1[\s>]")
RAW_PADDING_RE = re.compile(r"<div\s+style=\{\{\s*padding[:\s]")
FONT_FAMILY_RE = re.compile(r"fontFamily.*system.ui", re.IGNORECASE)


def check_file(path):
    """Return list of violation strings for a single file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    violations = []

    has_crown = bool(CROWN_IMPORT_RE.search(text))

    # All rules are conditional on absence of CrownLayout:
    # If you've imported CrownLayout, you've adopted the shell system.
    if has_crown:
        return violations

    for i, line in enumerate(lines, 1):
        if FONT_FAMILY_RE.search(line):
            violations.append(
                f"  L{i}: [font-shell] fontFamily system-ui without CrownLayout: "
                f"{line.strip()[:120]}"
            )
        if H1_RE.search(line):
            violations.append(
                f"  L{i}: [root-h1] <h1> without CrownLayout: "
                f"{line.strip()[:120]}"
            )
        if RAW_PADDING_RE.search(line):
            violations.append(
                f"  L{i}: [raw-wrapper] raw <div style={{padding:}} without CrownLayout: "
                f"{line.strip()[:120]}"
            )

    return violations


def main():
    pages = sorted(PAGES_DIR.glob("*.jsx"))
    if not pages:
        print(f"ERROR: No .jsx files found in {PAGES_DIR}")
        return 1

    all_violations = {}

    for page in pages:
        if page.name in SKIP:
            print(f"SKIP  {page.name}")
            continue

        violations = check_file(page)
        if violations:
            all_violations[page.name] = violations
        else:
            print(f"OK    {page.name}")

    if all_violations:
        print("\n--- UI Shell Gate FAILED ---")
        for fname, viols in all_violations.items():
            print(f"\n{fname}:")
            for v in viols:
                print(v)
        total = sum(len(v) for v in all_violations.values())
        print(
            f"\n{total} violation(s) in {len(all_violations)} file(s).\n"
            "Fix: import and wrap the page in CrownLayout.\n"
            "  Path: frontend/dashboards/src/components/crown/CrownLayout.jsx\n"
            "  Docs: docs/REFERENCE_MODULE_PATTERN.md"
        )
        return 1

    checked = len(pages) - len(SKIP)
    print(f"\nUI Shell Gate passed ({checked} files checked, {len(SKIP)} skipped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
