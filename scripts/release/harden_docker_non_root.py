from pathlib import Path

root = Path.cwd().resolve()
candidates = [root / "Dockerfile", root / "backend/Dockerfile"]
changed = []

# Fail before any write if a candidate can escape the checkout or is not a regular file.
for path in candidates:
    if (
        path.is_symlink()
        or path.parent.is_symlink()
        or not path.resolve(strict=False).is_relative_to(root)
        or (path.exists() and not path.is_file())
    ):
        raise SystemExit("Refusing unsafe Dockerfile path")

for path in candidates:
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    if "USER crownapp" in text:
        continue

    hardening = """
# Crown production hardening: run as non-root.
RUN addgroup --system crownapp || true \\
    && adduser --system --ingroup crownapp crownapp || true
USER crownapp
"""

    path.write_text(text.rstrip() + "\n\n" + hardening + "\n", encoding="utf-8")
    changed.append(str(path.relative_to(root)))

print("updated:", changed)
