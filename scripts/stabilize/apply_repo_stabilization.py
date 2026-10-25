from pathlib import Path
import json
import os
import re
import sys

ROOT = Path.cwd()
OUT = ROOT / "audit-artifacts" / "stabilization"
OUT.mkdir(parents=True, exist_ok=True)
A11Y = ROOT / "audit-artifacts" / "frontend-a11y"
A11Y.mkdir(parents=True, exist_ok=True)

changes = {
    "frontend_import_cleanup": [],
    "frontend_label_fix": [],
    "backend_schema_patch": [],
}

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def record(bucket: str, path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if rel not in changes[bucket]:
        changes[bucket].append(rel)

def remove_unused_react_imports():
    src = ROOT / "frontend" / "dashboards" / "src"
    for path in src.rglob("*"):
        if path.suffix not in {".js", ".jsx"}:
            continue
        text = read_text(path)
        if "React." in text:
            continue

        lines = text.splitlines()
        new_lines = []
        changed = False

        for line in lines:
            if re.fullmatch(r'\s*import React from ["\']react["\'];\s*', line):
                changed = True
                continue

            m = re.fullmatch(r'(\s*)import React,\s*\{(.*)\}\s*from ["\']react["\'];\s*', line)
            if m:
                indent, names = m.groups()
                new_lines.append(f"{indent}import {{{names}}} from \"react\";")
                changed = True
                continue

            new_lines.append(line)

        new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
        if changed and new_text != text:
            write_text(path, new_text)
            record("frontend_import_cleanup", path)

def fix_basic_labels():
    targets = [
        ROOT / "frontend" / "dashboards" / "src" / "pages" / "Student360Page.jsx",
        ROOT / "frontend" / "dashboards" / "src" / "pages" / "RoleDashboardPage.jsx",
        ROOT / "frontend" / "dashboards" / "src" / "pages" / "TranscriptRO.jsx",
    ]

    def safe_id(label: str, idx: int) -> str:
        label = re.sub(r"<[^>]+>", "", label).strip().lower()
        label = re.sub(r"[^a-z0-9_-]+", "-", label).strip("-")
        if not label:
            label = "field"
        return f"{label}-{idx}"

    missing_controls = []

    for path in targets:
        if not path.exists():
            continue

        lines = read_text(path).splitlines()
        changed = False

        for i in range(len(lines) - 1):
            label_line = lines[i]
            next_line = lines[i + 1]

            plain_label = re.search(r"<label(?![^>]*htmlFor=)(?![^>]*aria-label=)[^>]*>.*</label>", label_line)
            plain_control = re.search(r"<(input|select|textarea)(?![^>]*id=)\\b", next_line)

            if plain_label and plain_control:
                label_text_match = re.search(r"<label[^>]*>(.*?)</label>", label_line)
                label_text = label_text_match.group(1) if label_text_match else "field"
                control_id = safe_id(label_text, i + 1)
                lines[i] = re.sub(r"<label\\b", f'<label htmlFor="{control_id}"', label_line, count=1)
                lines[i + 1] = re.sub(r"<(input|select|textarea)\\b", rf'<\\1 id="{control_id}"', next_line, count=1)
                changed = True

        # scan likely MUI controls still missing labels
        for idx, line in enumerate(lines, start=1):
            if any(tag in line for tag in ("<TextField", "<Select", "<Autocomplete")):
                has_label = ("label=" in line) or ("aria-label=" in line) or ("\"aria-label\"" in line)
                if not has_label:
                    missing_controls.append(f"{path.relative_to(ROOT).as_posix()}:{idx}:{line.strip()}")

        new_text = "\n".join(lines) + "\n"
        if changed and new_text != read_text(path):
            write_text(path, new_text)
            record("frontend_label_fix", path)

    write_text(A11Y / "04_missing_control_labels.txt", "\n".join(missing_controls) + ("\n" if missing_controls else ""))

def insert_imports_after_top_block(text: str, import_lines: list[str]) -> str:
    missing = [line for line in import_lines if line not in text]
    if not missing:
        return text

    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
        elif insert_at > 0:
            break

    new_lines = lines[:insert_at] + missing + lines[insert_at:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")

def ensure_function_extend_schema(path: Path, func_name: str, decorator_line: str):
    if not path.exists():
        return

    text = read_text(path)
    original = text

    pattern = re.compile(
        rf'((?:^[ \t]*@[^\n]+\n)*)^[ \t]*def[ \t]+{re.escape(func_name)}\(',
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return

    block = match.group(1)
    block_lines = [ln for ln in block.splitlines(True) if "extend_schema(" not in ln]
    new_block = decorator_line + "\n" + "".join(block_lines)

    start, end = match.span(1)
    text = text[:start] + new_block + text[end:]

    if text != original:
        text = insert_imports_after_top_block(
            text,
            [
                "from drf_spectacular.types import OpenApiTypes",
                "from drf_spectacular.utils import extend_schema",
            ],
        )
        write_text(path, text)
        record("backend_schema_patch", path)

def ensure_class_serializer(path: Path, class_name: str, serializer_name: str):
    if not path.exists():
        return

    text = read_text(path)
    original = text

    pattern = re.compile(
        rf'(class\\s+{re.escape(class_name)}\\(APIView\\):[\\s\\S]*?permission_classes\\s*=\\s*\\[[^\\]]+\\]\\n)(?!\\s*serializer_class\\s*=)',
        re.MULTILINE,
    )

    text, count = pattern.subn(rf'\\1    serializer_class = {serializer_name}\\n', text, count=1)
    if count and text != original:
        write_text(path, text)
        record("backend_schema_patch", path)

def patch_spiritual_life():
    path = ROOT / "backend" / "spiritual_life" / "api" / "views.py"
    mappings = {
        "SpiritualProfileView": "StudentSpiritualProfileSerializer",
        "SpiritualProfileDetailView": "StudentSpiritualProfileSerializer",
        "SpiritualAssessmentListCreate": "SpiritualAssessmentSerializer",
        "ChapelEventListCreate": "ChapelEventSerializer",
        "ChapelEventDetail": "ChapelEventSerializer",
        "ChapelAttendanceListCreate": "ChapelAttendanceSerializer",
        "SmallGroupListCreate": "SmallGroupSerializer",
        "SmallGroupMemberListCreate": "SmallGroupMemberSerializer",
        "SmallGroupSessionListCreate": "SmallGroupSessionSerializer",
        "SmallGroupSessionAttendanceView": "SmallGroupAttendanceSerializer",
        "PrayerRequestListCreate": "PrayerRequestSerializer",
        "PrayerRequestDetail": "PrayerRequestSerializer",
        "PastoralNoteListCreate": "PastoralNoteSerializer",
        "PastoralNoteDetail": "PastoralNoteSerializer",
    }
    for cls, serializer in mappings.items():
        ensure_class_serializer(path, cls, serializer)

def patch_director_views():
    path = ROOT / "backend" / "crown_api" / "director_views.py"
    get_funcs = [
        "aid_summary",
        "finance_summary",
        "registrar_summary",
        "director_dashboard",
        "director_priority",
        "director_timeline",
    ]
    for fn in get_funcs:
        ensure_function_extend_schema(path, fn, "@extend_schema(responses=OpenApiTypes.OBJECT)")
    for fn in ["director_actions"]:
        ensure_function_extend_schema(path, fn, "@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)")

def patch_aftercare():
    path = ROOT / "backend" / "aftercare" / "api.py"
    for fn in ["program_config", "enrollments", "pickup_contacts", "checkin", "checkout", "incidents"]:
        ensure_function_extend_schema(path, fn, "@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)")

def patch_board_views():
    path = ROOT / "backend" / "board_oversight" / "views.py"
    for fn in ["board_metrics", "board_dashboard", "list_snapshots", "list_packets", "get_packet"]:
        ensure_function_extend_schema(path, fn, "@extend_schema(responses=OpenApiTypes.OBJECT)")

def patch_finance_api_views():
    path = ROOT / "backend" / "finance" / "api_views.py"
    for fn in ["obligations", "invoice_create_from_obligations", "payment_intent_create", "payment_settle", "refund_create", "donation_create"]:
        ensure_function_extend_schema(path, fn, "@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)")

def main():
    remove_unused_react_imports()
    fix_basic_labels()
    patch_spiritual_life()
    patch_director_views()
    patch_aftercare()
    patch_board_views()
    patch_finance_api_views()

    write_text(OUT / "01_stabilization_changes.json", json.dumps(changes, indent=2))
    print(json.dumps(changes, indent=2))

if __name__ == "__main__":
    main()
