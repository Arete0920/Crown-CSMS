from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "audit-artifacts" / "release-verify" / "release_package_readiness.json"

BACKEND_REQUIRED = [
    "drf-spectacular",
    "drf-spectacular-sidecar",
    "reportlab",
    "pytest-django",
]

# Load-test-only requirements (not backend runtime)
LOADTEST_REQUIRED = [
    "locust",
]

FRONTEND_REQUIRED_DEV = {
    "@axe-core/playwright": "^4.10.2",
}


def ensure_backend_requirements() -> list[str]:
    touched = []
    candidates = [ROOT / "backend" / "requirements.txt", ROOT / "requirements.txt"]
    target = None
    for candidate in candidates:
        if candidate.exists():
            target = candidate
            break
    if target is None:
        target = ROOT / "backend" / "requirements.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lowered = {ln.lower().split("==")[0].split(">=")[0].strip(): ln for ln in lines}

    for pkg in BACKEND_REQUIRED:
        if pkg not in lowered:
            lines.append(pkg)
            touched.append(pkg)

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return touched


def ensure_loadtest_requirements() -> list[str]:
    touched = []
    target = ROOT / "backend" / "requirements-loadtest.txt"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Load testing / release readiness\n", encoding="utf-8")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lowered = {ln.lower().split("==")[0].split(">=")[0].strip(): ln for ln in lines}

    for pkg in LOADTEST_REQUIRED:
        if pkg not in lowered:
            lines.append(pkg)
            touched.append(pkg)

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return touched


def ensure_frontend_package() -> list[str]:
    touched = []
    pkg_path = ROOT / "frontend" / "dashboards" / "package.json"
    if not pkg_path.exists():
        return touched

    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    dev = data.setdefault("devDependencies", {})
    for name, version in FRONTEND_REQUIRED_DEV.items():
        if name not in dev:
            dev[name] = version
            touched.append(name)

    scripts = data.setdefault("scripts", {})
    scripts.setdefault("test:release:routes", "playwright test tests/release-auth-golden-path.spec.ts")
    scripts.setdefault("test:release:a11y", "playwright test tests/release-accessibility.spec.ts")

    pkg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return touched


def main() -> None:
    report = {
        "backend_added": ensure_backend_requirements(),
        "loadtest_added": ensure_loadtest_requirements(),
        "frontend_added": ensure_frontend_package(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
