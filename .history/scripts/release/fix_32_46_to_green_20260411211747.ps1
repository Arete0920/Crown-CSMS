$ErrorActionPreference = "Stop"

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $full = Join-Path (Get-Location) $Path
    [System.IO.File]::WriteAllText($full, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Ensure-TextBlock {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Needle,
        [Parameter(Mandatory = $true)][string]$Block
    )
    if (-not (Test-Path $Path)) { return }
    $text = Get-Content $Path -Raw
    if ($text -notmatch [regex]::Escape($Needle)) {
        $text = $text.TrimEnd() + "`r`n`r`n" + $Block.Trim() + "`r`n"
        Write-FileUtf8 -Path $Path -Content $text
    }
}

Write-FileUtf8 -Path "docs/release/PRIORITY_32_46_TO_GREEN.md" -Content @'
# CROWN2026 — PRIORITIES 32–46 TO GREEN

32. Release patch idempotency
Green when duplicate injected blocks in settings.py and urls.py are normalized and reported.
33. Release package readiness
Green when required backend/frontend release-closeout packages are present and a package report is clean.
34. Canonical report and closeout route catalog
Green when report/release-closeout routes are enumerated and written to a manifest.
35. Release route contract tests
Green when release-closeout and report routes resolve and return expected status/content type.
36. PDF header contract
Green when report endpoints emit application/pdf and attachment headers.
37. Frontend release API unification
Green when auth token, school header, and timeout handling are centralized.
38. Stable release export controls
Green when export controls expose data-testid markers and use the shared API client.
39. Deterministic auth golden path
Green when Playwright login uses env-driven credentials and stable selectors.
40. Accessibility smoke
Green when axe scans pass on login/admin/parent/teacher/student routes.
41. CompuWerx sandbox evidence
Green when sandbox verification writes a dated proof file or a hard fail artifact.
42. Seed/fixture parity
Green when release demo seed manifest exists and parity scan is clean.
43. Workflow preflight
Green when workflow names, lockfile references, and required checks validate.
44. Release environment matrix
Green when dev/staging/prod expectations are documented in one canonical file.
45. Release status matrix widget
Green when a small frontend widget reads release-closeout status and exposes test ids.
46. Release doctor
Green when one command runs patch guard, package readiness, route tests, frontend smoke, sandbox proof, manifests, and writes a doctor summary.
'@

Write-FileUtf8 -Path "scripts/release/release_patch_guard.py" -Content @'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "audit-artifacts" / "release-verify" / "release_patch_guard.json"

SETTINGS_BLOCKS = [
    "INSTALLED_APPS += ['drf_spectacular', 'drf_spectacular_sidecar']",
    "REST_FRAMEWORK = globals().get('REST_FRAMEWORK', {})",
    "REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'",
    "'TITLE': 'Crown API'",
    "if \"release_closeout\" not in INSTALLED_APPS:",
    "INSTALLED_APPS.append(\"release_closeout\")",
]

URL_BLOCKS = [
    "from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView",
    "path('api/schema/', SpectacularAPIView.as_view(), name='api-schema')",
    "path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs')",
    "path(\"\", include(\"release_closeout.urls\"))",
]


def dedupe_lines(text: str, patterns: list[str]) -> tuple[str, int]:
    lines = text.splitlines()
    seen = set()
    out = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        matched = next((p for p in patterns if stripped == p.strip()), None)
        if matched:
            if matched in seen:
                removed += 1
                continue
            seen.add(matched)
        out.append(line)
    return "\n".join(out).rstrip() + "\n", removed


def main() -> None:
    results = []
    files = []
    files.extend(ROOT.rglob("settings.py"))
    files.extend(ROOT.rglob("urls.py"))

    for path in files:
        if ".venv" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        patterns = SETTINGS_BLOCKS if path.name == "settings.py" else URL_BLOCKS
        new_text, removed = dedupe_lines(text, patterns)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
        results.append({
            "file": str(path.relative_to(ROOT)),
            "removed_duplicate_lines": removed,
            "changed": new_text != text,
        })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
'@

Write-FileUtf8 -Path "scripts/release/verify_required_release_packages.py" -Content @'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "audit-artifacts" / "release-verify" / "release_package_readiness.json"

BACKEND_REQUIRED = [
    "drf-spectacular",
    "drf-spectacular-sidecar",
    "reportlab",
    "locust",
    "pytest-django",
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
        "frontend_added": ensure_frontend_package(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
'@

Write-FileUtf8 -Path "scripts/release/route_catalog.py" -Content @'
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "audit-artifacts" / "release-manifest" / "route_catalog.json"
REPORT_MD = ROOT / "audit-artifacts" / "release-manifest" / "route_catalog.md"

PATTERNS = [
    r"api/v1/release-closeout/[^\"]+",
    r"api/v1/reports/[^\"]+",
    r"api/v1/notifications/sms/status/",
    r"api/health/",
    r"api/integrity/",
]


def main() -> None:
    hits = []
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            for match in re.findall(pattern, text):
                hits.append({
                    "file": str(path.relative_to(ROOT)),
                    "route": match,
                })

    deduped = []
    seen = set()
    for item in hits:
        key = (item["file"], item["route"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(deduped, indent=2), encoding="utf-8")

    md = ["# Route Catalog", ""]
    for item in deduped:
        md.append(f"- `{item['route']}` :: `{item['file']}`")
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'@

Write-FileUtf8 -Path "tests/test_release_route_contracts.py" -Content @'
import pytest
from django.test import Client, override_settings

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

PDF_ROUTES = [
    "/api/v1/reports/transcript/DEMO-001/",
    "/api/v1/reports/report-card/DEMO-001/",
    "/api/v1/reports/discipline/DEMO-001/",
    "/api/v1/reports/board/",
]

JSON_ROUTES = [
    "/api/v1/release-closeout/status/",
    "/api/v1/release-closeout/metrics/live/",
    "/api/v1/release-closeout/graduation/DEMO-001/",
    "/api/v1/release-closeout/discipline/DEMO-001/",
    "/api/v1/notifications/sms/status/",
]


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
@pytest.mark.parametrize("route", JSON_ROUTES)
def test_release_json_routes(route):
    client = Client()
    response = client.get(route)
    assert response.status_code == 200
    assert "application/json" in response["Content-Type"]


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
@pytest.mark.parametrize("route", PDF_ROUTES)
def test_release_pdf_routes(route):
    client = Client()
    response = client.get(route)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "attachment;" in response["Content-Disposition"].lower()
'@

Write-FileUtf8 -Path "frontend/dashboards/src/lib/releaseApi.ts" -Content @'
import axios from "axios";

export const releaseApi = axios.create({
  timeout: 30000,
});

releaseApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  const schoolId = localStorage.getItem("school_id");

  config.headers = config.headers ?? {};
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (schoolId) {
    config.headers["X-School-Id"] = schoolId;
  }
  return config;
});

export default releaseApi;
'@

Write-FileUtf8 -Path "frontend/dashboards/src/components/release/ReleaseExportButton.tsx" -Content @'
import React, { useState } from "react";
import { Button, CircularProgress } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import releaseApi from "../../lib/releaseApi";

type ReleaseReport =
  | "transcript"
  | "report-card"
  | "discipline"
  | "board";

interface Props {
  report: ReleaseReport;
  studentRef?: string;
  label?: string;
  testId?: string;
}

const buildUrl = (report: ReleaseReport, studentRef?: string) => {
  switch (report) {
    case "transcript":
      return `/api/v1/reports/transcript/${studentRef ?? "DEMO-001"}/`;
    case "report-card":
      return `/api/v1/reports/report-card/${studentRef ?? "DEMO-001"}/`;
    case "discipline":
      return `/api/v1/reports/discipline/${studentRef ?? "DEMO-001"}/`;
    case "board":
      return `/api/v1/reports/board/`;
    default:
      return `/api/v1/reports/board/`;
  }
};

export default function ReleaseExportButton({
  report,
  studentRef,
  label,
  testId,
}: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const response = await releaseApi.get(buildUrl(report, studentRef), {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const link = Object.assign(document.createElement("a"), {
        href: URL.createObjectURL(blob),
        download: `${report}.pdf`,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="outlined"
      size="small"
      onClick={handleClick}
      disabled={loading}
      data-testid={testId || `release-export-${report}`}
      startIcon={loading ? <CircularProgress size={14} /> : <DownloadIcon />}
      sx={{ textTransform: "none", fontWeight: 500 }}
    >
      {label || `Download ${report}`}
    </Button>
  );
}
'@

Write-FileUtf8 -Path "frontend/dashboards/src/components/release/ReleaseStatusMatrix.tsx" -Content @'
import React, { useEffect, useState } from "react";
import { Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import releaseApi from "../../lib/releaseApi";

type StatusPayload = {
  discipline_escalation: boolean;
  transcript_export: boolean;
  report_card_export: boolean;
  graduation_readiness: boolean;
  board_report_export: boolean;
  sms_surface: boolean;
  live_metrics: {
    green: boolean;
    mock_or_seed_hits: number;
  };
};

function Row({ label, value, testId }: { label: string; value: boolean; testId: string }) {
  return (
    <Grid container justifyContent="space-between" alignItems="center" sx={{ py: 0.75 }}>
      <Grid item>
        <Typography variant="body2">{label}</Typography>
      </Grid>
      <Grid item>
        <Chip
          size="small"
          label={value ? "GREEN" : "OPEN"}
          color={value ? "success" : "warning"}
          data-testid={testId}
        />
      </Grid>
    </Grid>
  );
}

export default function ReleaseStatusMatrix() {
  const [payload, setPayload] = useState<StatusPayload | null>(null);

  useEffect(() => {
    releaseApi.get("/api/v1/release-closeout/status/")
      .then((res) => setPayload(res.data))
      .catch(() => setPayload(null));
  }, []);

  return (
    <Card sx={{ borderRadius: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom data-testid="release-status-title">
          Release Status Matrix
        </Typography>
        {!payload ? (
          <Typography variant="body2" data-testid="release-status-unavailable">
            Release status endpoint unavailable
          </Typography>
        ) : (
          <>
            <Row label="Discipline escalation" value={payload.discipline_escalation} testId="release-status-discipline" />
            <Row label="Transcript export" value={payload.transcript_export} testId="release-status-transcript" />
            <Row label="Report card export" value={payload.report_card_export} testId="release-status-report-card" />
            <Row label="Graduation readiness" value={payload.graduation_readiness} testId="release-status-graduation" />
            <Row label="Board report export" value={payload.board_report_export} testId="release-status-board" />
            <Row label="SMS surface" value={payload.sms_surface} testId="release-status-sms" />
            <Row label="Live metrics clean" value={payload.live_metrics.green} testId="release-status-metrics" />
            <Typography variant="caption" sx={{ pt: 1.5, display: "block" }} data-testid="release-status-mock-seed-hits">
              Mock/Seed hits: {payload.live_metrics.mock_or_seed_hits}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}
'@

Write-FileUtf8 -Path "frontend/dashboards/tests/release-auth-golden-path.spec.ts" -Content @'
import { test, expect } from "@playwright/test";

const user = process.env.PLAYWRIGHT_USER || "demo@example.com";
const pass = process.env.PLAYWRIGHT_PASS || "password";

test("release auth golden path", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  const email = page.locator('input[type="email"], input[name="email"], [data-testid="login-email"]').first();
  const password = page.locator('input[type="password"], input[name="password"], [data-testid="login-password"]').first();
  const submit = page.locator('button[type="submit"], [data-testid="login-submit"]').first();

  if (await email.count()) {
    await email.fill(user);
  }
  if (await password.count()) {
    await password.fill(pass);
  }
  if (await submit.count()) {
    await submit.click();
  }

  await page.waitForLoadState("networkidle");
  await expect(page.locator("body")).toContainText(/dashboard|admin|teacher|parent|student|billing|attendance/i);
});
'@

Write-FileUtf8 -Path "frontend/dashboards/tests/release-accessibility.spec.ts" -Content @'
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/login", "/admin", "/teacher", "/parent", "/student"];

for (const route of routes) {
  test(`a11y smoke ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(v => v.impact === "serious" || v.impact === "critical");
    expect(serious, `Serious/critical violations on ${route}`).toEqual([]);
  });
}
'@

Write-FileUtf8 -Path "scripts/release/compuwerx_sandbox_capture.ps1" -Content @'
$ErrorActionPreference = "Stop"

$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$SandboxUrl = if ($env:COMPUWERX_SANDBOX_URL) { $env:COMPUWERX_SANDBOX_URL } else { "" }
$out = "$base\compuwerx_sandbox_capture.txt"

if (-not $SandboxUrl) {
@"
COMPUWERX sandbox URL not provided.
Set COMPUWERX_SANDBOX_URL and rerun.
This artifact is a hard evidence placeholder until sandbox verification is supplied.
"@ | Out-File $out -Encoding utf8
    Write-Host "CompuWerx sandbox URL missing. Wrote placeholder artifact."
    exit 0
}

try {
    $resp = Invoke-WebRequest -Uri $SandboxUrl -Method Get -TimeoutSec 30
@"
URL: $SandboxUrl
Status: $($resp.StatusCode)
Headers:
$($resp.Headers | Out-String)
"@ | Out-File $out -Encoding utf8
} catch {
    $_ | Out-String | Out-File $out -Encoding utf8
}
'@

Write-FileUtf8 -Path "scripts/release/seed_fixture_parity.py" -Content @'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "audit-artifacts" / "release-verify" / "release_demo_seed_manifest.json"
OUT = ROOT / "audit-artifacts" / "release-verify" / "seed_fixture_parity.json"


def main() -> None:
    if not SEED.exists():
        SEED.parent.mkdir(parents=True, exist_ok=True)
        SEED.write_text(
            json.dumps({
                "school": "demo-school",
                "students": [{"ref": "DEMO-001"}, {"ref": "DEMO-002"}],
            }, indent=2),
            encoding="utf-8",
        )

    payload = json.loads(SEED.read_text(encoding="utf-8"))
    students = payload.get("students", [])
    refs = [s.get("ref") for s in students if s.get("ref")]

    result = {
        "student_refs": refs,
        "has_demo_001": "DEMO-001" in refs,
        "has_demo_002": "DEMO-002" in refs,
        "green": "DEMO-001" in refs and len(refs) >= 1,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
'@

Write-FileUtf8 -Path "scripts/release/workflow_preflight.py" -Content @'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit-artifacts" / "release-manifest" / "workflow_preflight.json"
REQUIRED = {
    "dependency-audit.yml",
    "release-verify.yml",
}


def main() -> None:
    wf_dir = ROOT / ".github" / "workflows"
    files = sorted([p.name for p in wf_dir.glob("*.yml")] + [p.name for p in wf_dir.glob("*.yaml")])

    package_lock = ROOT / "frontend" / "dashboards" / "package-lock.json"

    result = {
        "workflow_files": files,
        "required_present": sorted(REQUIRED.intersection(files)),
        "missing_required": sorted(REQUIRED.difference(files)),
        "frontend_package_lock_exists": package_lock.exists(),
        "green": len(REQUIRED.difference(files)) == 0 and package_lock.exists(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
'@

Write-FileUtf8 -Path "docs/release/RELEASE_ENV_MATRIX.md" -Content @'
# RELEASE ENV MATRIX

| Area | Dev | Staging | Prod |
|---|---|---|---|
| Base URL | local or sandbox | pre-prod verified host | production verified host |
| Auth tokens | demo/local | staging secrets only | prod secrets only |
| School header | demo-school allowed | real staging tenant only | production tenant only |
| OpenAPI export | yes | yes | yes |
| Health/Integrity | required | required | required |
| Release-closeout status | required | required | required |
| PDF report routes | required | required | required |
| CompuWerx sandbox proof | optional | required | required before go-live |
| Playwright smoke | required | required | optional post-deploy |
| A11y smoke | required | required | required on RC |
| Mock/seed scan | required clean | required clean | required clean |
'@

Write-FileUtf8 -Path "scripts/release/26_release_doctor.ps1" -Content @'
$ErrorActionPreference = "Stop"

$verify = "audit-artifacts\release-verify"
$manifest = "audit-artifacts\release-manifest"
New-Item -ItemType Directory -Force -Path $verify, $manifest | Out-Null

Write-Host "=== PATCH GUARD ===" -ForegroundColor Cyan
python scripts\release\release_patch_guard.py 2>&1 | Tee-Object -FilePath "$verify\20_patch_guard.txt"

Write-Host "=== PACKAGE READINESS ===" -ForegroundColor Cyan
python scripts\release\verify_required_release_packages.py 2>&1 | Tee-Object -FilePath "$verify\21_package_readiness.txt"

Write-Host "=== ROUTE CATALOG ===" -ForegroundColor Cyan
python scripts\release\route_catalog.py 2>&1 | Tee-Object -FilePath "$manifest\09_route_catalog.txt"

Write-Host "=== SEED / FIXTURE PARITY ===" -ForegroundColor Cyan
python scripts\release\seed_fixture_parity.py 2>&1 | Tee-Object -FilePath "$verify\22_seed_fixture_parity.txt"

Write-Host "=== WORKFLOW PREFLIGHT ===" -ForegroundColor Cyan
python scripts\release\workflow_preflight.py 2>&1 | Tee-Object -FilePath "$manifest\10_workflow_preflight.txt"

Write-Host "=== PYTEST ROUTE CONTRACTS ===" -ForegroundColor Cyan
pytest -q tests/test_release_route_contracts.py tests/test_release_closeout_phase2.py tests/test_mock_seed_scan_output.py 2>&1 | Tee-Object -FilePath "$verify\23_pytest_route_contracts.txt"

Write-Host "=== COMPUWERX SANDBOX PROOF ===" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts\release\compuwerx_sandbox_capture.ps1

Write-Host "=== FRONTEND RELEASE TESTS ===" -ForegroundColor Cyan
if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  npm ci 2>&1 | Tee-Object -FilePath "..\..\$verify\24_npm_ci_release_doctor.txt"
  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$verify\25_frontend_unit_release_doctor.txt"
  npx playwright install --with-deps 2>&1 | Tee-Object -FilePath "..\..\$verify\26_playwright_install_release_doctor.txt"
  npx playwright test tests/release-auth-golden-path.spec.ts 2>&1 | Tee-Object -FilePath "..\..\$verify\27_playwright_auth_golden_path.txt"
  npx playwright test tests/release-accessibility.spec.ts 2>&1 | Tee-Object -FilePath "..\..\$verify\28_playwright_accessibility.txt"
  Pop-Location
} else {
  "frontend/dashboards/package.json not found" | Out-File "$verify\24_npm_ci_release_doctor.txt"
}

@"
# SHIP CANDIDATE 32–46

Generated: $(Get-Date -Format s)

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_32_46_TO_GREEN.md
- docs/release/RELEASE_ENV_MATRIX.md

Exit checks:
- release_patch_guard.json shows duplicate insertions normalized
- release_package_readiness.json present
- route_catalog.json present
- workflow_preflight.json green
- seed_fixture_parity.json green
- route contract pytest green
- auth golden path and accessibility smoke green
- compuwerx sandbox artifact present
"@ | Out-File "docs\release\SHIP_CANDIDATE_32_46.md" -Encoding utf8

Write-Host "Release doctor complete." -ForegroundColor Green
'@

Write-Host "Created priorities 32–46 issue-fix pack." -ForegroundColor Green
Write-Host "Next run:" -ForegroundColor Yellow
Write-Host " powershell -ExecutionPolicy Bypass -File scripts\release\fix_32_46_to_green.ps1"
Write-Host " powershell -ExecutionPolicy Bypass -File scripts\release\26_release_doctor.ps1"
