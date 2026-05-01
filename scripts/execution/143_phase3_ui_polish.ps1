$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ============================================================
# CROWN PHASE 3 - UI POLISH IMPLEMENTATION + NON-AZURE PROOF
# Run from repo root in VS Code PowerShell.
# Does not touch Azure.
# ============================================================

Set-Location (git rev-parse --show-toplevel)
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path
$Out = "audit-artifacts\nonazure-phase3-ui-polish\$Stamp"
$Docs = "docs\crown-master-binder"
$Design = "$Docs\design-system"
$Ops = "$Docs\operations"
$Inventory = "$Docs\inventory"

New-Item -ItemType Directory -Force -Path $Out, $Design, $Ops, $Inventory | Out-Null
Start-Transcript -Path "$Out\00_PHASE3_RUN_LOG.txt" -Force | Out-Null

Write-Host "CROWN Phase 3 UI polish implementation"
Write-Host "Repo: $Root"
Write-Host "Output: $Out"

# ------------------------------------------------------------
# 01. Repo state
# ------------------------------------------------------------
$Branch = git branch --show-current
$HeadBefore = git rev-parse --short HEAD

git status --short | Set-Content "$Out\01_git_status_before.txt" -Encoding UTF8
git log --oneline -20 | Set-Content "$Out\02_recent_commits.txt" -Encoding UTF8

# ------------------------------------------------------------
# 02. Detect frontend root
# ------------------------------------------------------------
$PackageFiles = Get-ChildItem -Recurse -File -Filter package.json |
  Where-Object { $_.FullName -notmatch "\\node_modules\\" }

$FrontendRoot = $null
$FrontendPackage = $null
foreach ($pkg in $PackageFiles) {
  try {
    $raw = Get-Content $pkg.FullName -Raw
    $lower = $raw.ToLowerInvariant()
    if ($lower -match "react|vite|next|tailwind|@types/react") {
      $FrontendRoot = Split-Path $pkg.FullName -Parent
      $FrontendPackage = $pkg.FullName
      break
    }
  }
  catch {}
}

if (-not $FrontendRoot) {
  "# STOP`n`nNo React/Vite/Next frontend package.json detected." |
    Set-Content "$Out\STOP_NO_FRONTEND_FOUND.md" -Encoding UTF8
  code "$Out\STOP_NO_FRONTEND_FOUND.md"
  throw "No React/Vite/Next frontend package.json detected."
}

$SrcRoot = Join-Path $FrontendRoot "src"
if (-not (Test-Path $SrcRoot)) {
  $SrcRoot = $FrontendRoot
}

$StylesDir = Join-Path $SrcRoot "styles"
$ComponentsDir = Join-Path $SrcRoot "components\crown"
$UtilsDir = Join-Path $SrcRoot "lib\crown"
New-Item -ItemType Directory -Force -Path $StylesDir, $ComponentsDir, $UtilsDir | Out-Null

@"
FrontendRoot=$FrontendRoot
FrontendPackage=$FrontendPackage
SrcRoot=$SrcRoot
StylesDir=$StylesDir
ComponentsDir=$ComponentsDir
UtilsDir=$UtilsDir
"@ | Set-Content "$Out\03_frontend_detection.txt" -Encoding UTF8

# ------------------------------------------------------------
# 03. Create/replace CROWN visual system files
# ------------------------------------------------------------
$ThemeCss = @'
:root {
  --crown-bg: #f7faff;
  --crown-bg-soft: #eef5ff;
  --crown-surface: #ffffff;
  --crown-surface-soft: #f4f8ff;
  --crown-border: #d8e6ff;
  --crown-border-strong: #b8d4ff;
  --crown-primary: #3b82f6;
  --crown-primary-strong: #2563eb;
  --crown-primary-deep: #1d4ed8;
  --crown-primary-soft: #dbeafe;
  --crown-primary-faint: #eff6ff;
  --crown-accent: #8b5cf6;
  --crown-accent-soft: #ede9fe;
  --crown-gold: #d99a2b;
  --crown-gold-soft: #fff3d6;
  --crown-success: #16a34a;
  --crown-success-soft: #dcfce7;
  --crown-warning: #d97706;
  --crown-warning-soft: #fef3c7;
  --crown-danger: #dc2626;
  --crown-danger-soft: #fee2e2;
  --crown-text: #172033;
  --crown-muted: #5f6f89;
  --crown-subtle: #8291aa;
  --crown-radius-sm: 10px;
  --crown-radius-md: 14px;
  --crown-radius-lg: 20px;
  --crown-radius-xl: 28px;
  --crown-shadow-soft: 0 8px 24px rgba(37, 99, 235, 0.08);
  --crown-shadow-card: 0 16px 40px rgba(37, 99, 235, 0.10);
  --crown-shadow-lift: 0 22px 58px rgba(37, 99, 235, 0.14);
}

html {
  background: var(--crown-bg);
}

body {
  background:
    radial-gradient(circle at 10% 0%, rgba(59, 130, 246, 0.14), transparent 32rem),
    radial-gradient(circle at 90% 5%, rgba(139, 92, 246, 0.09), transparent 30rem),
    linear-gradient(180deg, var(--crown-bg) 0%, var(--crown-bg-soft) 100%);
  color: var(--crown-text);
  text-rendering: optimizeLegibility;
}

a {
  color: var(--crown-primary-strong);
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}

button,
[role="button"],
a,
input,
select,
textarea {
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    border-color 140ms ease,
    background-color 140ms ease,
    color 140ms ease;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.34);
  outline-offset: 2px;
}

.crown-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 10%, rgba(59, 130, 246, 0.13), transparent 28rem),
    radial-gradient(circle at 85% 0%, rgba(139, 92, 246, 0.08), transparent 32rem),
    linear-gradient(180deg, var(--crown-bg) 0%, var(--crown-bg-soft) 100%);
  color: var(--crown-text);
}

.crown-shell {
  width: min(1440px, calc(100% - 32px));
  margin: 0 auto;
  padding: 24px 0 48px;
}

.crown-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--crown-border);
  border-radius: var(--crown-radius-lg);
  box-shadow: var(--crown-shadow-card);
  backdrop-filter: blur(10px);
}

.crown-card-soft {
  background: linear-gradient(180deg, #ffffff 0%, var(--crown-surface-soft) 100%);
  border: 1px solid var(--crown-border);
  border-radius: var(--crown-radius-lg);
  box-shadow: var(--crown-shadow-soft);
}

.crown-card-section {
  padding: 22px;
}

.crown-page-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.crown-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--crown-primary-strong);
  background: var(--crown-primary-faint);
  border: 1px solid var(--crown-border);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.crown-title {
  margin: 10px 0 6px;
  color: var(--crown-text);
  font-size: clamp(28px, 3vw, 42px);
  line-height: 1.05;
  font-weight: 850;
  letter-spacing: -0.035em;
}

.crown-subtitle {
  max-width: 780px;
  color: var(--crown-muted);
  font-size: 16px;
  line-height: 1.6;
}

.crown-grid {
  display: grid;
  gap: 18px;
}

.crown-grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.crown-grid-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.crown-grid-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.crown-kpi {
  padding: 18px;
}

.crown-kpi-label {
  color: var(--crown-muted);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.crown-kpi-value {
  margin-top: 8px;
  color: var(--crown-text);
  font-size: 34px;
  line-height: 1;
  font-weight: 850;
  letter-spacing: -0.035em;
}

.crown-kpi-context {
  margin-top: 10px;
  color: var(--crown-muted);
  font-size: 14px;
  line-height: 1.45;
}

.crown-button-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--crown-primary-strong);
  border-radius: 14px;
  background: linear-gradient(180deg, var(--crown-primary) 0%, var(--crown-primary-strong) 100%);
  color: #ffffff;
  min-height: 42px;
  padding: 10px 16px;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22);
  text-decoration: none;
}

.crown-button-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 32px rgba(37, 99, 235, 0.28);
}

.crown-button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--crown-border-strong);
  border-radius: 14px;
  background: #ffffff;
  color: var(--crown-primary-strong);
  min-height: 42px;
  padding: 10px 16px;
  font-weight: 800;
  text-decoration: none;
}

.crown-button-secondary:hover {
  background: var(--crown-primary-faint);
  transform: translateY(-1px);
}

.crown-status {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid transparent;
  white-space: nowrap;
}

.crown-status-pass {
  background: var(--crown-success-soft);
  color: #166534;
  border-color: #bbf7d0;
}

.crown-status-review {
  background: var(--crown-warning-soft);
  color: #92400e;
  border-color: #fde68a;
}

.crown-status-fail {
  background: var(--crown-danger-soft);
  color: #991b1b;
  border-color: #fecaca;
}

.crown-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
  border: 1px solid var(--crown-border);
  border-radius: var(--crown-radius-lg);
  background: #ffffff;
}

.crown-table th {
  background: var(--crown-primary-faint);
  color: var(--crown-text);
  text-align: left;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 12px 14px;
  border-bottom: 1px solid var(--crown-border);
}

.crown-table td {
  padding: 13px 14px;
  border-bottom: 1px solid var(--crown-border);
  color: var(--crown-text);
}

.crown-empty-state {
  padding: 32px;
  text-align: center;
  border: 1px dashed var(--crown-border-strong);
  border-radius: var(--crown-radius-lg);
  background: rgba(255, 255, 255, 0.78);
}

.crown-form-control {
  width: 100%;
  border: 1px solid var(--crown-border-strong);
  border-radius: 14px;
  background: #ffffff;
  color: var(--crown-text);
  min-height: 42px;
  padding: 10px 12px;
}

.crown-form-label {
  display: block;
  color: var(--crown-text);
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 6px;
}

.crown-form-help {
  color: var(--crown-muted);
  font-size: 13px;
  line-height: 1.45;
  margin-top: 6px;
}

@media (max-width: 1080px) {
  .crown-grid-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .crown-grid-3 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .crown-shell {
    width: min(100% - 20px, 1440px);
    padding-top: 16px;
  }

  .crown-grid-2,
  .crown-grid-3,
  .crown-grid-4 {
    grid-template-columns: 1fr;
  }

  .crown-page-header {
    flex-direction: column;
  }

  .crown-title {
    font-size: 30px;
  }
}
'@

$ThemePath = Join-Path $StylesDir "crown-theme.css"
$ThemeCss | Set-Content $ThemePath -Encoding UTF8

$IndexTs = @'
export { CrownPageHeader } from "./CrownPageHeader";
export { CrownKpiCard } from "./CrownKpiCard";
export { CrownEmptyState } from "./CrownEmptyState";
export { CrownStatusPill } from "./CrownStatusPill";
export { CrownDashboardFrame } from "./CrownDashboardFrame";
'@

$CrownPageHeader = @'
import React from "react";

type CrownPageHeaderProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export function CrownPageHeader({
  eyebrow = "CROWN",
  title,
  subtitle,
  action,
}: CrownPageHeaderProps) {
  return (
    <header className="crown-page-header">
      <div>
        <div className="crown-eyebrow">{eyebrow}</div>
        <h1 className="crown-title">{title}</h1>
        {subtitle ? <p className="crown-subtitle">{subtitle}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </header>
  );
}
'@

$CrownKpiCard = @'
import React from "react";

type CrownKpiCardProps = {
  label: string;
  value: string | number;
  context?: string;
  status?: "pass" | "review" | "fail";
};

export function CrownKpiCard({
  label,
  value,
  context,
  status = "review",
}: CrownKpiCardProps) {
  const statusLabel =
    status === "pass" ? "On Track" : status === "fail" ? "Needs Action" : "Review";

  return (
    <section className="crown-card crown-kpi">
      <div className="flex items-start justify-between gap-3">
        <div className="crown-kpi-label">{label}</div>
        <span className={`crown-status crown-status-${status}`}>{statusLabel}</span>
      </div>
      <div className="crown-kpi-value">{value}</div>
      {context ? <div className="crown-kpi-context">{context}</div> : null}
    </section>
  );
}
'@

$CrownEmptyState = @'
import React from "react";

type CrownEmptyStateProps = {
  title: string;
  message: string;
  action?: React.ReactNode;
};

export function CrownEmptyState({ title, message, action }: CrownEmptyStateProps) {
  return (
    <section className="crown-empty-state">
      <h2 className="text-xl font-bold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">{message}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </section>
  );
}
'@

$CrownStatusPill = @'
import React from "react";

type CrownStatusPillProps = {
  status: "pass" | "review" | "fail";
  children: React.ReactNode;
};

export function CrownStatusPill({ status, children }: CrownStatusPillProps) {
  return <span className={`crown-status crown-status-${status}`}>{children}</span>;
}
'@

$CrownDashboardFrame = @'
import React from "react";
import { CrownPageHeader } from "./CrownPageHeader";

type CrownDashboardFrameProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
};

export function CrownDashboardFrame({
  eyebrow = "CROWN",
  title,
  subtitle,
  action,
  children,
}: CrownDashboardFrameProps) {
  return (
    <main className="crown-page">
      <div className="crown-shell">
        <CrownPageHeader eyebrow={eyebrow} title={title} subtitle={subtitle} action={action} />
        {children}
      </div>
    </main>
  );
}
'@

$CrownUiUtils = @'
export type CrownStatus = "pass" | "review" | "fail";

export function crownStatusFromBoolean(value: boolean | null | undefined): CrownStatus {
  if (value === true) return "pass";
  if (value === false) return "fail";
  return "review";
}

export function crownFormatCount(value: number | null | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "0";
  return new Intl.NumberFormat("en-US").format(value);
}

export function crownClassName(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
'@

$FilesToWrite = @{
  (Join-Path $ComponentsDir "index.ts") = $IndexTs
  (Join-Path $ComponentsDir "CrownPageHeader.tsx") = $CrownPageHeader
  (Join-Path $ComponentsDir "CrownKpiCard.tsx") = $CrownKpiCard
  (Join-Path $ComponentsDir "CrownEmptyState.tsx") = $CrownEmptyState
  (Join-Path $ComponentsDir "CrownStatusPill.tsx") = $CrownStatusPill
  (Join-Path $ComponentsDir "CrownDashboardFrame.tsx") = $CrownDashboardFrame
  (Join-Path $UtilsDir "ui.ts") = $CrownUiUtils
}

foreach ($path in $FilesToWrite.Keys) {
  $FilesToWrite[$path] | Set-Content $path -Encoding UTF8
}

# ------------------------------------------------------------
# 04. Patch global CSS import safely
# ------------------------------------------------------------
$GlobalCssCandidates = @(
  (Join-Path $SrcRoot "index.css"),
  (Join-Path $SrcRoot "globals.css"),
  (Join-Path $SrcRoot "global.css"),
  (Join-Path $SrcRoot "App.css"),
  (Join-Path $SrcRoot "app\globals.css"),
  (Join-Path $SrcRoot "app\global.css")
)

$PatchedGlobalCss = @()
foreach ($candidate in $GlobalCssCandidates) {
  if (Test-Path $candidate) {
    $content = Get-Content $candidate -Raw
    if ($content -notmatch "crown-theme\.css") {
      $relativeImport = "./styles/crown-theme.css"
      $candidateDir = Split-Path $candidate -Parent
      if ((Resolve-Path $candidateDir).Path -like "*\\app") {
        $relativeImport = "../styles/crown-theme.css"
      }
      $newContent = "@import `"$relativeImport`";`n" + $content
      $newContent | Set-Content $candidate -Encoding UTF8
      $PatchedGlobalCss += $candidate
    }
    else {
      $PatchedGlobalCss += "$candidate already imported"
    }
  }
}

if ($PatchedGlobalCss.Count -eq 0) {
  $newGlobal = Join-Path $SrcRoot "index.css"
  "@import `"./styles/crown-theme.css`";`n" | Set-Content $newGlobal -Encoding UTF8
  $PatchedGlobalCss += $newGlobal
}

$PatchedGlobalCss | Set-Content "$Out\04_patched_global_css.txt" -Encoding UTF8

# ------------------------------------------------------------
# 05. Brand cleanup in public-facing frontend/docs strings only
# ------------------------------------------------------------
$BrandScanExtensions = @(".tsx", ".jsx", ".html", ".md", ".css")
$BrandFiles = Get-ChildItem $SrcRoot, $Docs -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $BrandScanExtensions -contains $_.Extension.ToLowerInvariant() -and
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\audit-artifacts\\"
  }

$BrandChanges = @()
foreach ($file in $BrandFiles) {
  $before = Get-Content $file.FullName -Raw
  $after = $before
  $after = $after -replace "Crown2026", "CROWN"
  $after = $after -replace "Crown 2026", "CROWN"
  $after = $after -replace "CROWN 2026", "CROWN"
  $after = $after -replace "Crown School Redesign Strategy", "CROWN Strategy"

  if ($after -ne $before) {
    $after | Set-Content $file.FullName -Encoding UTF8
    $BrandChanges += [pscustomobject]@{
      File = $file.FullName.Replace($Root, "").TrimStart("\\")
      Action = "Public-facing brand string normalized to CROWN"
    }
  }
}

$BrandChanges | Export-Csv "$Out\05_brand_cleanup_changes.csv" -NoTypeInformation

# ------------------------------------------------------------
# 06. Scan important UI/release risks after changes
# ------------------------------------------------------------
$ScanFiles = Get-ChildItem $SrcRoot -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.Extension.ToLowerInvariant() -in @(".tsx", ".jsx", ".ts", ".js", ".css", ".html", ".md")
  }

function Search-Hits {
  param(
    [array]$Files,
    [array]$Patterns,
    [string]$Type
  )

  $rows = @()
  foreach ($file in $Files) {
    try {
      $hits = Select-String -Path $file.FullName -Pattern $Patterns -AllMatches -ErrorAction SilentlyContinue
      foreach ($hit in $hits) {
        $rows += [pscustomobject]@{
          Type = $Type
          File = $file.FullName.Replace($Root, "").TrimStart("\\")
          Line = $hit.LineNumber
          Text = $hit.Line.Trim()
        }
      }
    }
    catch {}
  }

  return $rows
}

$PlaceholderPatterns = @(
  "TODO",
  "FIXME",
  "TBD",
  "coming soon",
  "placeholder",
  "lorem",
  "dummy",
  "fake",
  "not implemented",
  "hardcoded",
  "replace me",
  "needs wiring"
)

$UiRiskPatterns = @(
  "href=\"#\"",
  "href='#'",
  "javascript:void",
  "bg-gray-900",
  "bg-slate-900",
  "bg-zinc-900",
  "bg-neutral-900",
  "#000000",
  "#111827",
  "#0f172a",
  "navy",
  "dark placeholder"
)

$RoutePatterns = @(
  "<Route",
  "path=",
  "path:",
  "href=",
  "to=",
  "navigate\(",
  "router.push",
  "createBrowserRouter"
)

$DashboardPatterns = @(
  "dashboard",
  "Dashboard",
  "kpi",
  "KPI",
  "metric",
  "Metric",
  "widget",
  "Widget"
)

$WizardPatterns = @(
  "wizard",
  "Wizard",
  "stepper",
  "Stepper",
  "multi-step",
  "multistep"
)

$PlaceholderHits = Search-Hits -Files $ScanFiles -Patterns $PlaceholderPatterns -Type "Placeholder"
$UiRiskHits = Search-Hits -Files $ScanFiles -Patterns $UiRiskPatterns -Type "UI Risk"
$RouteHits = Search-Hits -Files $ScanFiles -Patterns $RoutePatterns -Type "Route"
$DashboardHits = Search-Hits -Files $ScanFiles -Patterns $DashboardPatterns -Type "Dashboard"
$WizardHits = Search-Hits -Files $ScanFiles -Patterns $WizardPatterns -Type "Wizard"

$PlaceholderHits | Export-Csv "$Out\06_placeholder_hits_after.csv" -NoTypeInformation
$UiRiskHits | Export-Csv "$Out\07_ui_risk_hits_after.csv" -NoTypeInformation
$RouteHits | Export-Csv "$Out\08_route_hits_after.csv" -NoTypeInformation
$DashboardHits | Export-Csv "$Out\09_dashboard_hits_after.csv" -NoTypeInformation
$WizardHits | Export-Csv "$Out\10_wizard_hits_after.csv" -NoTypeInformation

Copy-Item "$Out\08_route_hits_after.csv" "$Inventory\06_ROUTE_INVENTORY_AFTER_PHASE3.csv" -Force
Copy-Item "$Out\09_dashboard_hits_after.csv" "$Inventory\07_DASHBOARD_INVENTORY_AFTER_PHASE3.csv" -Force
Copy-Item "$Out\10_wizard_hits_after.csv" "$Inventory\08_WIZARD_INVENTORY_AFTER_PHASE3.csv" -Force

# ------------------------------------------------------------
# 07. Generate UI adoption guide
# ------------------------------------------------------------
$Guide = @"
# CROWN Phase 3 UI Polish Adoption Guide

Generated: $(Get-Date -Format s)

## Installed Files
- $ThemePath
- $ComponentsDir\CrownDashboardFrame.tsx
- $ComponentsDir\CrownPageHeader.tsx
- $ComponentsDir\CrownKpiCard.tsx
- $ComponentsDir\CrownEmptyState.tsx
- $ComponentsDir\CrownStatusPill.tsx
- $ComponentsDir\index.ts
- $UtilsDir\ui.ts

## Global CSS Import Status
$($PatchedGlobalCss -join "`n")

## Required Usage Pattern

```tsx
import { CrownDashboardFrame, CrownKpiCard, CrownEmptyState } from "@/components/crown";

export function AdminDashboard() {
  return (
    <CrownDashboardFrame
      eyebrow="CROWN"
      title="School Administrator Dashboard"
      subtitle="Operational view for enrollment, student records, billing, communications, and school health."
    >
      <section className="crown-grid crown-grid-4">
        <CrownKpiCard label="Enrollment" value="428" context="Seeded sandbox data" status="review" />
        <CrownKpiCard label="Attendance" value="96%" context="Today" status="pass" />
        <CrownKpiCard label="Billing" value="$0" context="No overdue sandbox balances" status="pass" />
        <CrownKpiCard label="Open Tasks" value="12" context="Admissions and records" status="review" />
      </section>
    </CrownDashboardFrame>
  );
}
```

## Production UI Rules
- Do not use navy-heavy or black dashboard backgrounds.
- Do not leave placeholder or fake metrics unmarked.
- Do not use dead links such as href="#".
- Do not create a new visual system per module.
- Use CROWN light royal colors, soft cards, clean spacing, and shared status pills.
- Empty states must explain next action.
- Error states must be actionable and never expose raw stack/debug text.
- Role dashboards must feel purpose-built.

## Remaining Review Counts After Phase 3
- Placeholder hits: $($PlaceholderHits.Count)
- UI risk hits: $($UiRiskHits.Count)
- Route references: $($RouteHits.Count)
- Dashboard references: $($DashboardHits.Count)
- Wizard references: $($WizardHits.Count)

## Evidence Files
- $Out\06_placeholder_hits_after.csv
- $Out\07_ui_risk_hits_after.csv
- $Out\08_route_hits_after.csv
- $Out\09_dashboard_hits_after.csv
- $Out\10_wizard_hits_after.csv
"@

$GuidePath = "$Design\05_PHASE3_UI_POLISH_ADOPTION_GUIDE.md"
$Guide | Set-Content $GuidePath -Encoding UTF8
Copy-Item $GuidePath "$Out\11_PHASE3_UI_POLISH_ADOPTION_GUIDE.md" -Force

# ------------------------------------------------------------
# 08. Detect and run validation scripts
# ------------------------------------------------------------
$Validation = @()

function Add-ValidationResult {
  param(
    [string]$Area,
    [string]$Command,
    [string]$Status,
    [int]$ExitCode,
    [string]$OutputFile
  )

  $script:Validation += [pscustomobject]@{
    Area = $Area
    Command = $Command
    Status = $Status
    ExitCode = $ExitCode
    OutputFile = $OutputFile
  }
}

$Pkg = Get-Content $FrontendPackage -Raw | ConvertFrom-Json
$Scripts = @()
if ($Pkg.scripts) {
  foreach ($p in $Pkg.scripts.PSObject.Properties) {
    if ($p.Name -in @("typecheck", "lint", "build", "test")) {
      $Scripts += $p.Name
    }
  }
}

Push-Location $FrontendRoot
try {
  $idx = 0
  foreach ($scriptName in $Scripts) {
    $idx++
    $cmd = "npm run $scriptName"
    $log = Join-Path $Root "$Out\validation_frontend_$($idx)_$($scriptName).txt"

    "=== COMMAND ===" | Set-Content $log -Encoding UTF8
    $cmd | Add-Content $log -Encoding UTF8
    "" | Add-Content $log -Encoding UTF8
    "=== OUTPUT ===" | Add-Content $log -Encoding UTF8

    $prevErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    cmd.exe /c $cmd >> $log 2>&1
    $ErrorActionPreference = $prevErrorActionPreference
    $exit = $LASTEXITCODE
    $status = if ($exit -eq 0) { "PASS" } else { "FAIL" }
    Add-ValidationResult "Frontend" $cmd $status $exit $log
  }
}
finally {
  Pop-Location
}

if ($Validation.Count -eq 0) {
  Add-ValidationResult "Frontend" "No npm validation scripts detected" "REVIEW" 0 "$Out\03_frontend_detection.txt"
}

$Validation | Export-Csv "$Out\12_validation_results.csv" -NoTypeInformation

# ------------------------------------------------------------
# 09. Build release blocker board
# ------------------------------------------------------------
$Blockers = @()

function Add-Blocker {
  param(
    [string]$Priority,
    [string]$Area,
    [string]$Issue,
    [string]$Owner,
    [string]$Evidence,
    [string]$RequiredFix
  )

  $script:Blockers += [pscustomobject]@{
    Priority = $Priority
    Area = $Area
    Issue = $Issue
    Owner = $Owner
    Evidence = $Evidence
    RequiredFix = $RequiredFix
    Status = "Open"
  }
}

foreach ($v in $Validation | Where-Object { $_.Status -eq "FAIL" }) {
  Add-Blocker "P0" "Frontend validation" "Validation failed: $($v.Command)" "Dev 4 / Dev 5" $v.OutputFile "Fix validation failure and rerun Phase 3."
}

if ($PlaceholderHits.Count -gt 0) {
  Add-Blocker "P1" "Placeholder cleanup" "$($PlaceholderHits.Count) placeholder/incomplete markers remain." "Dev 4 / Dev 5" "$Out\06_placeholder_hits_after.csv" "Remove, replace, or formally defer production-facing markers."
}

if ($UiRiskHits.Count -gt 0) {
  Add-Blocker "P1" "UI polish" "$($UiRiskHits.Count) UI risk hits remain." "Dev 4" "$Out\07_ui_risk_hits_after.csv" "Fix dead links, off-brand dark treatments, and hardcoded visual drift."
}

if ($DashboardHits.Count -eq 0) {
  Add-Blocker "P1" "Dashboard inventory" "No dashboard references detected after scan." "Dev 4" "$Out\09_dashboard_hits_after.csv" "Confirm dashboard naming/routes and update inventory."
}

if ($WizardHits.Count -eq 0) {
  Add-Blocker "P2" "Wizard inventory" "No wizard references detected after scan." "Dev 4" "$Out\10_wizard_hits_after.csv" "Confirm whether wizards exist under another naming pattern."
}

$Blockers | Sort-Object Priority, Area | Export-Csv "$Out\13_PHASE3_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\13_PHASE3_BLOCKER_BOARD.csv" "$Ops\12_PHASE3_BLOCKER_BOARD.csv" -Force

# ------------------------------------------------------------
# 10. Summary and commit gate
# ------------------------------------------------------------
$ValidationFailCount = @($Validation | Where-Object { $_.Status -eq "FAIL" }).Count
$ValidationPassCount = @($Validation | Where-Object { $_.Status -eq "PASS" }).Count
$P0Count = @($Blockers | Where-Object { $_.Priority -eq "P0" }).Count
$P1Count = @($Blockers | Where-Object { $_.Priority -eq "P1" }).Count
$P2Count = @($Blockers | Where-Object { $_.Priority -eq "P2" }).Count

$Decision = if ($P0Count -eq 0 -and $ValidationFailCount -eq 0) {
  "PHASE3_UI_POLISH_COMMIT_ELIGIBLE"
}
else {
  "PHASE3_UI_POLISH_REMEDIATION_REQUIRED"
}

$Summary = @"
# CROWN Phase 3 UI Polish Summary

Generated: $(Get-Date -Format s)
Repo: $Root
Branch: $Branch
Head Before: $HeadBefore
Frontend Root: $FrontendRoot

## Decision
$Decision

## What Was Implemented
- Added global CROWN light royal theme CSS.
- Added reusable CROWN dashboard/page/KPI/status/empty-state components.
- Added CROWN UI utility helpers.
- Patched global CSS import.
- Normalized public-facing Crown2026/Crown 2026 references to CROWN in frontend/docs text files.
- Regenerated route, dashboard, and wizard inventories.
- Ran available frontend validation scripts.

## Counts
- Brand cleanup files changed: $($BrandChanges.Count)
- Placeholder hits remaining: $($PlaceholderHits.Count)
- UI risk hits remaining: $($UiRiskHits.Count)
- Route references: $($RouteHits.Count)
- Dashboard references: $($DashboardHits.Count)
- Wizard references: $($WizardHits.Count)
- Validation PASS: $ValidationPassCount
- Validation FAIL: $ValidationFailCount
- P0 blockers: $P0Count
- P1 blockers: $P1Count
- P2 blockers: $P2Count

## Key Files
- UI adoption guide: $GuidePath
- Validation results: $Out\12_validation_results.csv
- Blocker board: $Out\13_PHASE3_BLOCKER_BOARD.csv
- Placeholder scan: $Out\06_placeholder_hits_after.csv
- UI risk scan: $Out\07_ui_risk_hits_after.csv
- Dashboard inventory: $Out\09_dashboard_hits_after.csv
- Wizard inventory: $Out\10_wizard_hits_after.csv

## Required Next Move
- If P0 is zero and validation passed, review/commit the UI polish changes.
- If P0 exists, fix those first, rerun this script, then commit.

## Validation Results
$($Validation | Format-Table -AutoSize | Out-String)

## Blocker Board
$($Blockers | Sort-Object Priority, Area | Format-Table -AutoSize | Out-String)
"@

$SummaryPath = "$Out\99_PHASE3_SUMMARY.md"
$Summary | Set-Content $SummaryPath -Encoding UTF8
Copy-Item $SummaryPath "$Ops\13_CURRENT_PHASE3_UI_POLISH_SUMMARY.md" -Force

git status --short | Set-Content "$Out\90_git_status_after_changes.txt" -Encoding UTF8

if ($P0Count -eq 0 -and $ValidationFailCount -eq 0) {
  git add "$ThemePath" "$ComponentsDir" "$UtilsDir" "$Docs" 2>$null
  git add --force "$Out" 2>$null

  foreach ($changed in $BrandChanges) {
    $f = Join-Path $Root $changed.File
    if (Test-Path $f) {
      git add "$f" 2>$null
    }
  }

  foreach ($css in $PatchedGlobalCss) {
    $cssPath = $css -replace " already imported", ""
    if (Test-Path $cssPath) {
      git add "$cssPath" 2>$null
    }
  }

  git diff --cached --name-only | Set-Content "$Out\91_staged_files.txt" -Encoding UTF8
  $staged = git diff --cached --name-only
  if ($staged) {
    git commit -m "style: add CROWN UI polish system and proof pack"
    git rev-parse --short HEAD | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
  }
  else {
    "No staged changes to commit." | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
  }
}
else {
  @"
Commit intentionally skipped.
Reason:
P0 blockers: $P0Count
Validation failures: $ValidationFailCount
Fix blocker board and rerun Phase 3 before committing UI code changes.
"@ | Set-Content "$Out\92_commit_skipped.txt" -Encoding UTF8
}

git status --short | Set-Content "$Out\93_git_status_final.txt" -Encoding UTF8

# ------------------------------------------------------------
# 11. Open outputs
# ------------------------------------------------------------
code "$SummaryPath"
code "$Out\13_PHASE3_BLOCKER_BOARD.csv"
code "$Out\12_validation_results.csv"
code "$GuidePath"
code "$Out\93_git_status_final.txt"

Write-Host ""
Write-Host "CROWN Phase 3 complete."
Write-Host "Decision: $Decision"
Write-Host "Output: $Out"
Write-Host ""
Write-Host "Open first:"
Write-Host "$SummaryPath"
Write-Host "$Out\13_PHASE3_BLOCKER_BOARD.csv"

Stop-Transcript | Out-Null
