"""
Crown Permission Audit
Heuristic scan: find DRF ViewSets/APIViews missing CrownModulePermission or permission_classes.
Run from repo root: python tools/audit/perm_audit.py
"""
import re
import glob
from pathlib import Path

targets = []
for pat in [
    "backend/**/api.py",
    "backend/**/api_views.py",
    "backend/**/viewsets.py",
    "backend/**/views*.py",
]:
    targets += [Path(p) for p in glob.glob(pat, recursive=True)]


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1", errors="ignore")


re_class = re.compile(r"^\s*class\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*:", re.M)
re_api_view = re.compile(r"^\s*@api_view\(\[([^\]]+)\]\)", re.M)
re_perm_deco = re.compile(r"^\s*@permission_classes\(\[([^\]]*)\]\)", re.M)
re_crown_perm = re.compile(r"CrownModulePermission\(", re.M)
re_perm_classes_attr = re.compile(r"^\s*permission_classes\s*=\s*\[([^\]]*)\]", re.M)

findings = []
counts = {"files": 0, "classes": 0, "fbv": 0, "missing": 0}

DRF_BASES = ["ViewSet", "APIView", "GenericAPIView", "ModelViewSet", "ReadOnlyModelViewSet"]

for p in sorted(set(targets)):
    rel = str(p).replace("\\", "/")
    txt = read(p)
    if "migrations" in rel or "tests" in rel:
        continue
    counts["files"] += 1

    class_hits = list(re_class.finditer(txt))
    if class_hits:
        counts["classes"] += len(class_hits)
        file_has_crown = bool(re_crown_perm.search(txt))
        file_has_perm_attr = bool(re_perm_classes_attr.search(txt))
        for m in class_hits:
            cls, bases = m.group(1), m.group(2)
            drf_like = any(k in bases for k in DRF_BASES)
            if drf_like and not file_has_crown and not file_has_perm_attr:
                findings.append(
                    f"[MISSING-CLASS] {rel} :: class {cls}({bases.strip()}) — no CrownModulePermission, no permission_classes"
                )
                counts["missing"] += 1
            elif drf_like and file_has_crown:
                # Crown is present somewhere — check per-class if permission_classes appears
                # before next class (narrow window)
                start = m.start()
                end_next = next(
                    (n.start() for n in re_class.finditer(txt) if n.start() > start),
                    len(txt),
                )
                block = txt[start:end_next]
                if not re_crown_perm.search(block) and not re_perm_classes_attr.search(block):
                    findings.append(
                        f"[MISSING-CLASS] {rel} :: class {cls}({bases.strip()}) — CrownModulePermission in file but NOT in this class block"
                    )
                    counts["missing"] += 1

    fbv_hits = list(re_api_view.finditer(txt))
    if fbv_hits:
        counts["fbv"] += len(fbv_hits)
        has_perm_deco = bool(re_perm_deco.search(txt))
        if not has_perm_deco:
            for h in fbv_hits:
                post = txt[h.end():]
                mdef = re.search(r"^\s*def\s+([A-Za-z0-9_]+)\s*\(", post, re.M)
                fn = mdef.group(1) if mdef else "unknown"
                findings.append(
                    f"[MISSING-FBV]   {rel} :: @api_view def {fn}() — no @permission_classes on any FBV in file"
                )
                counts["missing"] += 1

# Group by app
by_app: dict[str, list[str]] = {}
for f in findings:
    parts = f.split("/")
    app = parts[1] if len(parts) > 2 else "?"
    by_app.setdefault(app, []).append(f)

lines = []
lines.append("CROWN PERMISSION AUDIT (heuristic)")
lines.append("=" * 70)
lines.append(f"Scanned files : {counts['files']}")
lines.append(f"Classes found : {counts['classes']}")
lines.append(f"FBVs found    : {counts['fbv']}")
lines.append(f"Missing flags : {counts['missing']}")
lines.append("")
lines.append("Findings by app:")
lines.append("-" * 70)
if by_app:
    for app in sorted(by_app):
        lines.append(f"\n[app: {app}]  ({len(by_app[app])} issues)")
        for f in by_app[app]:
            lines.append(f"  {f}")
else:
    lines.append("(none — all DRF endpoints have permission gates)")
lines.append("")
lines.append("=" * 70)
print("\n".join(lines))
