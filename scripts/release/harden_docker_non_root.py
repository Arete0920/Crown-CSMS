from pathlib import Path

candidates = [Path("Dockerfile"), Path("backend/Dockerfile")]
changed = []

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
    changed.append(str(path))

print("updated:", changed)
