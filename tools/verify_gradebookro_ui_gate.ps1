# tools/verify_gradebookro_ui_gate.ps1
# GradebookRO UI Surface Gate (static)
# Enforces minimum demo-ready UI surface on GradebookRO.jsx:
# - Must use CrownLayout
# - Must expose a print affordance (window.print or equivalent)
# - Must render a table-like gradebook surface (table OR grid)
# ASCII-only, PS5.1-safe, UTF-8 output.

$ErrorActionPreference = "Stop"

$repoRoot  = Split-Path -Parent $PSScriptRoot
$targetRel = "frontend/dashboards/src/pages/GradebookRO.jsx"
$target    = Join-Path $repoRoot $targetRel

if (!(Test-Path $target)) {
  Write-Host "GradebookRO UI Gate FAILED - missing file: $targetRel" -ForegroundColor Red
  exit 1
}

$raw = Get-Content -Path $target -Raw

# --- REQUIRED: CrownLayout ---
$reHasCrown = '\bCrownLayout\b'
if ($raw -notmatch $reHasCrown) {
  Write-Host "GradebookRO UI Gate FAILED - CrownLayout not found in GradebookRO.jsx" -ForegroundColor Red
  exit 1
}

# --- REQUIRED: Print affordance ---
# Accept either direct window.print(), or a handler calling it.
$rePrint = '\bwindow\.print\s*\('
if ($raw -notmatch $rePrint) {
  Write-Host "GradebookRO UI Gate FAILED - window.print() not found (print affordance missing)" -ForegroundColor Red
  exit 1
}

# --- REQUIRED: Table-like surface ---
# Accept <table, or role=table/grid, or CSS grid usage as fallback.
$reTableLike = '(?is)(<table\b|role\s*=\s*[''"](table|grid)[''"]|display\s*:\s*[''"]?grid[''"]?)'
if ($raw -notmatch $reTableLike) {
  Write-Host "GradebookRO UI Gate FAILED - no table/grid surface detected" -ForegroundColor Red
  exit 1
}

# --- BASIC sanity: title/header presence (keep loose) ---
# We don''t force exact wording; just require some H1/H2 element exists.
$reHeader = '(?is)<h1\b|<h2\b'
if ($raw -notmatch $reHeader) {
  Write-Host "GradebookRO UI Gate FAILED - missing <h1> or <h2> header" -ForegroundColor Red
  exit 1
}

Write-Host "GradebookRO UI Gate PASSED" -ForegroundColor Green
