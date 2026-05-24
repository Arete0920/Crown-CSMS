# tools/verify_ui_shell_gate.ps1
# Static UI Shell Gate (Crown dashboards)
# - Enforces: pages that ALREADY use CrownLayout must not reintroduce "system-ui wrapper" patterns
# - Skips: MUI pages, LoginPage.jsx
# - Designed to PASS on current main while preventing regressions.

$ErrorActionPreference = "Stop"

# Repo root = parent of /tools
$repoRoot = Split-Path -Parent $PSScriptRoot
$pagesDir = Join-Path $repoRoot "frontend/dashboards/src/pages"

if (!(Test-Path $pagesDir)) {
  throw "pages dir not found: $pagesDir"
}

# Explicit exclusions
$excludedNames = @(
  "LoginPage.jsx"
)

# Regex helpers (single-quoted = literal strings)
$reIsMUI        = '@mui/material'
$reHasCrown     = '\bCrownLayout\b'

# Bad wrapper patterns we want to prevent from coming back.
# ['"] in single-quoted PS = literal ['"] regex char class matching single OR double quote.
$reSystemUi     = 'fontFamily\s*:\s*[''"][^''"]*system-ui[^''"]*[''"]'
$rePadFontBlock = 'style\s*=\s*\{\{\s*[^}]*padding\s*:\s*(?:16|24|[''"]?2rem[''"]?)\s*,\s*[^}]*fontFamily\s*:'

$violations = New-Object System.Collections.Generic.List[object]
$checked = 0
$skipped = 0

Get-ChildItem -Path $pagesDir -Filter "*.jsx" -File | ForEach-Object {
  $file = $_
  $name = $file.Name

  if ($excludedNames -contains $name) {
    $skipped++
    return
  }

  $raw = Get-Content -Path $file.FullName -Raw

  # Skip MUI pages
  if ($raw -match $reIsMUI) {
    $skipped++
    return
  }

  # Only enforce pages that already adopted CrownLayout
  if ($raw -notmatch $reHasCrown) {
    $skipped++
    return
  }

  $checked++
  $hits = @()

  if ($raw -match $reSystemUi) {
    $hits += "Contains system-ui fontFamily (forbidden in CrownLayout pages)"
  }

  if ($raw -match $rePadFontBlock) {
    $hits += "Contains padding+fontFamily inline wrapper style={{...}} (forbidden in CrownLayout pages)"
  }

  if ($hits.Count -gt 0) {
    $lineHits = @()
    $lineHits += (Select-String -Path $file.FullName -Pattern 'fontFamily\s*:' -AllMatches -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty LineNumber)
    $lineHits += (Select-String -Path $file.FullName -Pattern 'style\s*=\s*\{\{' -AllMatches -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty LineNumber)
    $lineHits = $lineHits | Sort-Object -Unique

    $linesStr = if ($lineHits.Count -gt 0) { $lineHits -join "," } else { "" }
    $violations.Add([pscustomobject]@{
      File  = $name
      Hits  = ($hits -join "; ")
      Lines = $linesStr
    }) | Out-Null
  }
}

Write-Host "UI Shell Gate: checked=$checked, skipped=$skipped" -ForegroundColor Cyan

if ($violations.Count -gt 0) {
  Write-Host ""
  Write-Host "UI Shell Gate FAILED - regressions detected in CrownLayout pages:" -ForegroundColor Red
  Write-Host ""
  $violations | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host ""
  Write-Host "Fix: remove system-ui wrappers and padding+fontFamily inline shells from the flagged pages (CrownLayout supplies the shell)." -ForegroundColor Yellow
  exit 1
}

Write-Host "UI Shell Gate PASSED" -ForegroundColor Green
