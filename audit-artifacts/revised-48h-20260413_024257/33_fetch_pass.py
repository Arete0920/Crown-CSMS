from pathlib import Path
import re

root = Path(r"C:\crown2026_recovery\wt_20260413_024257") / "frontend" / "dashboards" / "src"
changed = []
for path in root.rglob("*"):
    if path.suffix not in {".js", ".jsx"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    new_text = re.sub(r'(?<![A-Za-z0-9_$.])fetch\(', 'window.fetch(', text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        changed.append(str(path.relative_to(Path(r"C:\crown2026_recovery\wt_20260413_024257"))))
Path(r"C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\audit-artifacts\revised-48h-20260413_024257\33_fetch_pass_targets.txt").write_text("\n".join(changed), encoding="utf-8")
print(len(changed))