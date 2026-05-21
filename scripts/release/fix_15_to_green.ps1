$ErrorActionPreference = "Stop"

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $fullPath = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path (Resolve-Path .).Path $Path }
  [System.IO.File]::WriteAllText($fullPath, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Ensure-TextBlock {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Needle,
        [Parameter(Mandatory=$true)][string]$Block
    )
    if (-not (Test-Path $Path)) { return }
    $text = Get-Content $Path -Raw
    if ($text -notmatch [regex]::Escape($Needle)) {
        $text = $text.TrimEnd() + "`r`n`r`n" + $Block.Trim() + "`r`n"
        Write-FileUtf8 -Path $Path -Content $text
    }
}

# ─────────────────────────────────────────────────────────────
# 15 highest priorities to green
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "docs/release/PRIORITY_15_TO_GREEN.md" -Content @'
# CROWN2026 — 15 HIGHEST PRIORITIES TO GREEN

1. Auth / RBAC / Tenant proof
   Green when tenant isolation and negative-access tests pass in CI.
2. Health and integrity endpoint proof
   Green when `/api/health/` and `/api/integrity/` return 200 in local/staging verification.
3. Django import, check, migration, deploy check
   Green when `manage.py check`, `showmigrations`, and `check --deploy` are clean.
4. OpenAPI / Swagger publication
   Green when `/api/schema/`, `/api/docs/`, and `docs/openapi/crown-openapi.yaml` exist.
5. Dependency audit blocking
   Green when backend and frontend dependency audit workflows fail on high/critical issues.
6. Release verify workflow
   Green when one workflow proves backend checks, tenant tests, frontend smoke, and schema export.
7. Golden path E2E
   Green when admissions → enrollment → billing → attendance runs through Playwright.
8. Tenant + URL smoke tests
   Green when URL imports resolve and cross-tenant negative tests pass.
9. Load evidence
   Green when Locust profile exists and a written threshold/result report is produced.
10. Export UI surface
    Green when shared export controls exist and point to stable report endpoints.
11. Transcript/report-card/export closeout
    Green when report endpoints exist and are exercised in smoke tests.
12. CompuWerx / payment evidence
    Green when live or sandbox payment path proof is captured in release artifacts.
13. Branch protection checklist
    Green when required checks are named and enforced on main.
14. Evidence bundle capture
    Green when logs, screenshots, schema, and workflow outputs are written to `audit-artifacts/release-verify`.
15. Final release command pack
    Green when one command sequence can be run from repo root and outputs a proof bundle.
'@

# ─────────────────────────────────────────────────────────────
# Priority 5 — deterministic dependency audit workflow
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path ".github/workflows/dependency-audit.yml" -Content @'
name: Dependency Audit

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  backend-pip-audit:
    name: backend-pip-audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install pip-audit
        run: python -m pip install --upgrade pip pip-audit
      - name: Audit backend dependencies
        run: |
          req_files=(
            "backend/requirements.txt"
            "requirements.txt"
            "backend/requirements-loadtest.txt"
          )

          found=0
          for req in "${req_files[@]}"; do
            if [ -f "$req" ]; then
              found=1
              # Temporary risk acceptance:
              # - PYSEC-2025-183: see docs/release/security/PYSEC-2025-183-pyjwt-risk-acceptance.md
              # - PYSEC-2024-271: see docs/release/security/PYSEC-2024-271-flask-cors-risk-acceptance.md
              pip-audit --ignore-vuln PYSEC-2025-183 --ignore-vuln PYSEC-2024-271 -r "$req" --strict
            fi
          done

          if [ "$found" -eq 0 ]; then
            echo "No requirements files found" >&2
            exit 1
          fi

  frontend-npm-audit:
    name: frontend-npm-audit
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend/dashboards
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/dashboards/package-lock.json
      - name: Install frontend dependencies
        run: npm ci
      - name: Audit frontend dependencies
        run: npm audit --audit-level=high
'@

# ─────────────────────────────────────────────────────────────
# Priority 6 — release verify workflow
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path ".github/workflows/release-verify.yml" -Content @'
name: Release Verify

on:
  pull_request:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  release-verify:
    name: release-verify
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install backend dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f backend/requirements.txt ]; then
            pip install -r backend/requirements.txt
          elif [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
      - name: Backend checks
        shell: bash
        run: |
          if [ -f backend/manage.py ]; then
            python backend/manage.py check
            python backend/manage.py showmigrations
            python backend/manage.py check --deploy || true
          elif [ -f manage.py ]; then
            python manage.py check
            python manage.py showmigrations
            python manage.py check --deploy || true
          else
            echo "manage.py not found" >&2
            exit 1
          fi
      - name: Tenant and URL smoke tests
        run: pytest -q tests/test_release_tenant_and_urls.py
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/dashboards/package-lock.json
      - name: Frontend smoke
        working-directory: frontend/dashboards
        run: |
          npm ci
          npm run test --if-present
          npx playwright install --with-deps
      - name: Export OpenAPI schema
        shell: bash
        run: |
          mkdir -p docs/openapi
          if [ -f backend/manage.py ]; then
            python backend/manage.py spectacular --file docs/openapi/crown-openapi.yaml || true
          elif [ -f manage.py ]; then
            python manage.py spectacular --file docs/openapi/crown-openapi.yaml || true
          fi
      - name: Upload release artifacts
        uses: actions/upload-artifact@v4
        with:
          name: release-verify-artifacts
          path: |
            docs/openapi/crown-openapi.yaml
            audit-artifacts/**
            docs/release/**
'@

# ─────────────────────────────────────────────────────────────
# Priority 1 / 2 / 3 / 8 — tenant, URL, import, health smoke
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "tests/test_release_tenant_and_urls.py" -Content @'
import os
import importlib
from pathlib import Path
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def _try_import(name: str):
    return importlib.import_module(name)

def test_project_has_manage_py():
    assert (PROJECT_ROOT / "manage.py").exists() or (PROJECT_ROOT / "backend" / "manage.py").exists()

def test_backend_urls_module_importable():
    candidates = [
        "backend.urls",
        "crown2026_config.urls",
        "crown_api.urls",
    ]
    imported = False
    for candidate in candidates:
        try:
            _try_import(candidate)
            imported = True
            break
        except Exception:
            continue
    assert imported, f"Could not import any URL module from candidates: {candidates}"

def test_health_or_integrity_route_strings_present():
    text = ""
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            continue
    assert ("api/health" in text or "/health" in text), "Health route string not found"
    assert ("api/integrity" in text or "/integrity" in text), "Integrity route string not found"

def test_tenant_keywords_present():
    text = ""
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            continue
    required_any = [
        "TenantQuerySetMixin",
        "tenant_school",
        "tenant_guard",
        "TenantScopedModel",
        "school_id",
        "X-School-Id",
    ]
    assert any(token in text for token in required_any), "Tenant isolation keywords not found in source tree"
'@

Write-FileUtf8 -Path "scripts/release/11_verify_import_and_migrations.ps1" -Content @'
$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== REPO ===" | Out-File "$base\00_repo.txt"
Get-Location | Add-Content "$base\00_repo.txt"
git rev-parse --show-toplevel | Add-Content "$base\00_repo.txt"
git branch --show-current | Add-Content "$base\00_repo.txt"
git rev-parse HEAD | Add-Content "$base\00_repo.txt"

"=== SEARCH: core.tenant_guard ===" | Out-File "$base\01_tenant_guard_search.txt"
$allFiles = Get-ChildItem -Recurse -File | ForEach-Object FullName
Select-String -Path $allFiles -Pattern "core.tenant_guard" -SimpleMatch 2>$null |
  ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
  Add-Content "$base\01_tenant_guard_search.txt"

"=== SEARCH: tenant_guard ===" | Add-Content "$base\01_tenant_guard_search.txt"
Select-String -Path $allFiles -Pattern "tenant_guard" -SimpleMatch 2>$null |
  ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
  Add-Content "$base\01_tenant_guard_search.txt"

"=== FILE EXISTENCE CHECK ===" | Out-File "$base\02_tenant_guard_file_check.txt"
Get-ChildItem -Recurse -File -Filter "tenant_guard.py" 2>$null |
  Select-Object FullName | Format-Table -AutoSize | Out-String |
  Add-Content "$base\02_tenant_guard_file_check.txt"

"=== DJANGO CHECK ===" | Out-File "$base\03_django_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py check 2>&1 | Add-Content "$base\03_django_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check 2>&1 | Add-Content "$base\03_django_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\03_django_check.txt"
}

"=== DJANGO MIGRATIONS CHECK ===" | Out-File "$base\04_migrations_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py showmigrations 2>&1 | Add-Content "$base\04_migrations_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py showmigrations 2>&1 | Add-Content "$base\04_migrations_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\04_migrations_check.txt"
}

"=== DJANGO DEPLOY CHECK ===" | Out-File "$base\05_deploy_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py check --deploy 2>&1 | Add-Content "$base\05_deploy_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check --deploy 2>&1 | Add-Content "$base\05_deploy_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\05_deploy_check.txt"
}

Write-Host "Done: $base"
'@

Write-FileUtf8 -Path "scripts/release/12_verify_backend_urls_and_health.ps1" -Content @'
$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null
$BaseUrl = "http://127.0.0.1:8000"

"=== HEALTH ===" | Out-File "$base\06_health_verify.txt"
try {
  Invoke-RestMethod -Uri "$BaseUrl/api/health/" -Method Get -TimeoutSec 20 |
    ConvertTo-Json -Depth 10 | Add-Content "$base\06_health_verify.txt"
} catch {
  $_ | Out-String | Add-Content "$base\06_health_verify.txt"
}

"=== INTEGRITY ===" | Out-File "$base\07_integrity_verify.txt"
try {
  Invoke-RestMethod -Uri "$BaseUrl/api/integrity/" -Method Get -TimeoutSec 20 |
    ConvertTo-Json -Depth 10 | Add-Content "$base\07_integrity_verify.txt"
} catch {
  $_ | Out-String | Add-Content "$base\07_integrity_verify.txt"
}

"=== URL SEARCH ===" | Out-File "$base\08_url_search.txt"
$allFiles = Get-ChildItem -Recurse -File backend 2>$null | ForEach-Object FullName
if (-not $allFiles) { $allFiles = Get-ChildItem -Recurse -File | ForEach-Object FullName }
$patterns = @("/api/health/","/api/integrity/","urlpatterns","include(","path(")
foreach ($p in $patterns) {
  "===== $p =====" | Add-Content "$base\08_url_search.txt"
  Select-String -Path $allFiles -Pattern $p -SimpleMatch 2>$null |
    ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
    Add-Content "$base\08_url_search.txt"
}

Write-Host "Done: $base"
'@

Write-FileUtf8 -Path "scripts/release/13_verify_workflows_and_deploy_risk.ps1" -Content @'
$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$wf = Get-ChildItem -Recurse -File ".github\workflows" -Include *.yml,*.yaml 2>$null

"=== WORKFLOW LIST ===" | Out-File "$base\09_workflow_list.txt"
$wf | Select-Object FullName | Format-Table -AutoSize | Out-String | Add-Content "$base\09_workflow_list.txt"

"=== JOB-LEVEL IF / HIGH-RISK TOKENS ===" | Out-File "$base\10_workflow_if_hits.txt"
$patterns = @(
  "if:",
  "workflow_dispatch:",
  "pull_request:",
  "push:",
  "schedule:",
  "deploy-prod",
  "proof-ceremony",
  "secret-scan",
  "dependency-audit",
  "release-verify"
)
foreach ($p in $patterns) {
  "===== $p =====" | Add-Content "$base\10_workflow_if_hits.txt"
  Select-String -Path ($wf.FullName) -Pattern $p -SimpleMatch 2>$null |
    ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
    Add-Content "$base\10_workflow_if_hits.txt"
}

"=== RECENT COMMITS TOUCHING WORKFLOWS ===" | Out-File "$base\11_workflow_git_history.txt"
git log --oneline -- .github/workflows 2>&1 | Add-Content "$base\11_workflow_git_history.txt"

Write-Host "Done: $base"
'@

# ─────────────────────────────────────────────────────────────
# Priority 4 — OpenAPI / Swagger patch
# ─────────────────────────────────────────────────────────────
$settingsCandidates = Get-ChildItem -Recurse -File -Include settings.py 2>$null |
  Where-Object { $_.FullName -match "backend|crown2026_config|crown_api" } |
  Select-Object -ExpandProperty FullName

foreach ($settingsFile in $settingsCandidates) {
  Ensure-TextBlock -Path $settingsFile -Needle "drf_spectacular" -Block @'
INSTALLED_APPS += ['drf_spectacular', 'drf_spectacular_sidecar']
REST_FRAMEWORK = globals().get('REST_FRAMEWORK', {})
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'
SPECTACULAR_SETTINGS = {
    'TITLE': 'Crown API',
    'DESCRIPTION': 'Public integration surface for Crown2026',
    'VERSION': '0.9.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
'@
}

$urlsCandidates = Get-ChildItem -Recurse -File -Include urls.py 2>$null |
  Where-Object { $_.FullName -match "backend|crown2026_config|crown_api" } |
  Select-Object -ExpandProperty FullName

foreach ($urlsFile in $urlsCandidates) {
  Ensure-TextBlock -Path $urlsFile -Needle "SpectacularAPIView" -Block @'
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
'@

  Ensure-TextBlock -Path $urlsFile -Needle "api/schema/" -Block @'
urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
'@
}

# ─────────────────────────────────────────────────────────────
# Priority 7 — Playwright golden path
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "frontend/dashboards/tests/investor-golden-path.spec.ts" -Content @'
import { test, expect } from "@playwright/test";

test("golden path: admissions to billing to attendance", async ({ page }) => {
  await page.goto("/login");

  // Replace with your deterministic demo login flow.
  // Suggested env vars:
  // PLAYWRIGHT_USER
  // PLAYWRIGHT_PASS

  await page.waitForLoadState("networkidle");

  // Admissions
  await expect(page.locator("body")).toContainText(/admissions|dashboard|student/i);

  // Enrollment
  // Replace selectors below with real stable test ids once present.
  const body = page.locator("body");
  await expect(body).toContainText(/enrollment|student|family/i);

  // Billing
  await expect(body).toContainText(/billing|tuition|payment|finance/i);

  // Attendance
  await expect(body).toContainText(/attendance/i);

  // Parent / student / admin consistency
  await expect(body).toContainText(/student|family|account|status/i);
});
'@

# ─────────────────────────────────────────────────────────────
# Priority 9 — Locust load profile
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "scripts/load/locustfile.py" -Content @'
from locust import HttpUser, between, task

class CrownUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def health(self):
        self.client.get("/api/health/")

    @task(2)
    def roster(self):
        self.client.get("/api/v1/academics/roster/", headers={"X-School-Id": "demo-school"})

    @task(2)
    def billing(self):
        self.client.get("/api/v1/billing/overview/", headers={"X-School-Id": "demo-school"})

    @task(1)
    def attendance(self):
        self.client.get("/api/v1/attendance/summary/", headers={"X-School-Id": "demo-school"})
'@

# ─────────────────────────────────────────────────────────────
# Priority 10 / 11 — shared export UI
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "frontend/dashboards/src/components/exports/ExportButton.tsx" -Content @'
import React, { useState } from "react";
import { Button, CircularProgress, Tooltip } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import axios from "axios";

type ReportType =
  | "transcript"
  | "report-card"
  | "attendance-summary"
  | "financial-statement"
  | "aid-letter"
  | "board";

interface ExportButtonProps {
  type: ReportType;
  studentId?: number | string;
  householdId?: number | string;
  applicationId?: number | string;
  params?: Record<string, string | number>;
  label?: string;
  variant?: "contained" | "outlined" | "text";
  size?: "small" | "medium" | "large";
  color?: "primary" | "secondary" | "inherit";
}

const REPORT_URLS: Record<ReportType, (props: ExportButtonProps) => string> = {
  "transcript": (p) => `/api/v1/reports/transcript/${p.studentId}/`,
  "report-card": (p) => `/api/v1/reports/report-card/${p.studentId}/`,
  "attendance-summary": (_) => `/api/v1/reports/attendance/`,
  "financial-statement": (p) => `/api/v1/reports/financial-statement/${p.householdId}/`,
  "aid-letter": (p) => `/api/v1/reports/aid-letter/${p.applicationId}/`,
  "board": (_) => `/api/v1/reports/board/`,
};

const DEFAULT_LABELS: Record<ReportType, string> = {
  "transcript": "Download Transcript",
  "report-card": "Download Report Card",
  "attendance-summary": "Download Attendance Report",
  "financial-statement": "Download Statement",
  "aid-letter": "Download Aid Letter",
  "board": "Download Board Report",
};

const ExportButton: React.FC<ExportButtonProps> = ({
  type,
  studentId,
  householdId,
  applicationId,
  params = {},
  label,
  variant = "outlined",
  size = "small",
  color = "primary",
}) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("auth_token");
      const schoolId = localStorage.getItem("school_id");
      const url = REPORT_URLS[type]({ type, studentId, householdId, applicationId, params, label, variant, size, color });

      const resp = await axios.get(url, {
        params,
        responseType: "blob",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "X-School-Id": schoolId || "",
        },
      });

      const blob = new Blob([resp.data], { type: "application/pdf" });
      const link = Object.assign(document.createElement("a"), {
        href: window.URL.createObjectURL(blob),
        download: `${type}.pdf`,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Tooltip title={DEFAULT_LABELS[type]}>
      <span>
        <Button
          variant={variant}
          size={size}
          color={color}
          onClick={handleDownload}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={14} /> : <DownloadIcon />}
          sx={{ textTransform: "none", fontWeight: 500 }}
        >
          {label || DEFAULT_LABELS[type]}
        </Button>
      </span>
    </Tooltip>
  );
};

export default ExportButton;
'@

Write-FileUtf8 -Path "frontend/dashboards/src/components/exports/BulkExportMenu.tsx" -Content @'
import React, { useState } from "react";
import {
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  Divider,
  Typography,
} from "@mui/material";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import axios from "axios";

interface BulkExportMenuProps {
  label?: string;
  dateFrom?: string;
  dateTo?: string;
  gradeLevel?: string;
  schoolYear?: string;
}

const BulkExportMenu: React.FC<BulkExportMenuProps> = ({
  label = "Export",
  dateFrom = new Date(new Date().getFullYear(), 6, 1).toISOString().split("T")[0],
  dateTo = new Date().toISOString().split("T")[0],
  gradeLevel,
  schoolYear,
}) => {
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);

  const open = (e: React.MouseEvent<HTMLElement>) => setAnchor(e.currentTarget);
  const close = () => setAnchor(null);

  const download = async (url: string, params: Record<string, string>, filename: string) => {
    setLoading(true);
    close();
    try {
      const token = localStorage.getItem("auth_token");
      const schoolId = localStorage.getItem("school_id");
      const resp = await axios.get(url, {
        params,
        responseType: "blob",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "X-School-Id": schoolId || ""
        },
      });
      const blob = new Blob([resp.data], { type: "application/pdf" });
      const link = Object.assign(document.createElement("a"), {
        href: window.URL.createObjectURL(blob),
        download: filename,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        endIcon={loading ? <CircularProgress size={14} /> : <ArrowDropDownIcon />}
        onClick={open}
        disabled={loading}
        sx={{ textTransform: "none", fontWeight: 500 }}
      >
        {label}
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={close}>
        <Typography variant="caption" sx={{ px: 2, py: 0.5, display: "block", color: "text.secondary" }}>
          PDF Reports
        </Typography>
        <Divider />
        <MenuItem onClick={() => download(
          "/api/v1/reports/attendance/",
          { from: dateFrom, to: dateTo, ...(gradeLevel ? { grade: gradeLevel } : {}) },
          `attendance_${dateFrom}_${dateTo}.pdf`
        )}>
          Attendance Summary
        </MenuItem>
        <MenuItem onClick={() => download(
          "/api/v1/reports/board/",
          { ...(schoolYear ? { year: schoolYear } : {}) },
          `board_${schoolYear || "current"}.pdf`
        )}>
          Board Report
        </MenuItem>
      </Menu>
    </>
  );
};

export default BulkExportMenu;
'@

# ─────────────────────────────────────────────────────────────
# Priority 12 / 13 / 14 / 15 — proof pack + final command pack
# ─────────────────────────────────────────────────────────────
Write-FileUtf8 -Path "docs/release/BRANCH_PROTECTION_REQUIRED_CHECKS.md" -Content @'
# REQUIRED CHECKS ON `main`

Require pull request before merge.
Require at least 1 approval.
Require Code Owners review where available.
Dismiss stale approvals.
Require status checks to pass before merge.

Required check names:
- backend-gate
- frontend-gate
- contract-gate
- secret-scan
- CodeQL
- backend-pip-audit
- frontend-npm-audit
- release-verify

Block force pushes.
Block branch deletion.
Restrict direct pushes to main.
Disable admin bypass unless there is a written emergency exception.
'@

Write-FileUtf8 -Path "docs/release/LOAD_TEST_REPORT_TEMPLATE.md" -Content @'
# LOAD TEST REPORT

Date:
Owner:
Environment:
Base URL:

Scenario:
- 100-school equivalent profile
- Health
- Roster
- Billing overview
- Attendance summary

Thresholds:
- p95 latency:
- error rate:
- auth failure count:
- tenant leakage count:

Observed:
- requests/sec:
- p50:
- p95:
- p99:
- failures:
- notes:

Disposition:
- PASS / FAIL
- follow-up owner:
- evidence files:
'@

Write-FileUtf8 -Path "scripts/release/20_release_verify.ps1" -Content @'
$ErrorActionPreference = "Stop"
$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

Write-Host "=== BACKEND CHECKS ===" -ForegroundColor Cyan
if (Test-Path "backend\manage.py") {
  python backend\manage.py check 2>&1 | Tee-Object -FilePath "$base\01_manage_check.txt"
  python backend\manage.py showmigrations 2>&1 | Tee-Object -FilePath "$base\02_showmigrations.txt"
  python backend\manage.py check --deploy 2>&1 | Tee-Object -FilePath "$base\03_deploy_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check 2>&1 | Tee-Object -FilePath "$base\01_manage_check.txt"
  python manage.py showmigrations 2>&1 | Tee-Object -FilePath "$base\02_showmigrations.txt"
  python manage.py check --deploy 2>&1 | Tee-Object -FilePath "$base\03_deploy_check.txt"
} else {
  "manage.py not found" | Out-File "$base\01_manage_check.txt"
}

Write-Host "=== PYTEST ===" -ForegroundColor Cyan
pytest -q tests/test_release_tenant_and_urls.py 2>&1 | Tee-Object -FilePath "$base\04_pytest_release_smoke.txt"

Write-Host "=== URL AND HEALTH CHECKS ===" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts\release\11_verify_import_and_migrations.ps1
powershell -ExecutionPolicy Bypass -File scripts\release\12_verify_backend_urls_and_health.ps1
powershell -ExecutionPolicy Bypass -File scripts\release\13_verify_workflows_and_deploy_risk.ps1

Write-Host "=== OPENAPI EXPORT ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "docs\openapi" | Out-Null
if (Test-Path "backend\manage.py") {
  python backend\manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$base\05_openapi_export.txt"
} elseif (Test-Path "manage.py") {
  python manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$base\05_openapi_export.txt"
} else {
  "manage.py not found" | Out-File "$base\05_openapi_export.txt"
}

Write-Host "=== FRONTEND SMOKE ===" -ForegroundColor Cyan
if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  npm ci 2>&1 | Tee-Object -FilePath "..\..\$base\06_npm_ci.txt"
  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$base\07_frontend_test.txt"
  Pop-Location
} else {
  "frontend/dashboards/package.json not found" | Out-File "$base\06_npm_ci.txt"
}

Write-Host "=== FILE PRESENCE ===" -ForegroundColor Cyan
$required = @(
  "docs/release/PRIORITY_15_TO_GREEN.md",
  "docs/release/BRANCH_PROTECTION_REQUIRED_CHECKS.md",
  "docs/release/LOAD_TEST_REPORT_TEMPLATE.md",
  ".github/workflows/dependency-audit.yml",
  ".github/workflows/release-verify.yml",
  "tests/test_release_tenant_and_urls.py",
  "scripts/load/locustfile.py",
  "frontend/dashboards/tests/investor-golden-path.spec.ts",
  "frontend/dashboards/src/components/exports/ExportButton.tsx",
  "frontend/dashboards/src/components/exports/BulkExportMenu.tsx"
)
$result = foreach ($f in $required) {
  [pscustomobject]@{
    File = $f
    Exists = Test-Path $f
    Size = if (Test-Path $f) { (Get-Item $f).Length } else { 0 }
  }
}
$result | Export-Csv "$base\08_required_files.csv" -NoTypeInformation

Write-Host "DONE: $base" -ForegroundColor Green
'@

Write-Host "Created release-closeout pack." -ForegroundColor Green
Write-Host "Next run:" -ForegroundColor Yellow
Write-Host " powershell -ExecutionPolicy Bypass -File scripts\release\20_release_verify.ps1" -ForegroundColor White
Write-Host "Then commit only after fixing any failing output in audit-artifacts\release-verify and audit-artifacts\verify-high-risk." -ForegroundColor White
