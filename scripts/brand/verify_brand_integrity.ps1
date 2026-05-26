$ErrorActionPreference = "Stop"
$fail = $false

$patterns = @(
  "Crown Christian School Systems",
  "Christian School Systems",
  "Crown 2026",
  "CROWN 2026",
  "placeholder-logo",
  "fake-logo",
  "temp-logo",
  "sample-logo",
  "microsoft-like",
  "fake microsoft",
  "generated microsoft"
)

$scanRoots = @(
  "frontend/dashboards/src/brand",
  "frontend/dashboards/src/components/brand",
  "frontend/dashboards/public/brand"
)

foreach ($pattern in $patterns) {
  $matches = rg -n --hidden --glob '!node_modules/**' --glob '!.git/**' --glob '!audit-artifacts/**' --glob '!**/*.test.*' $pattern $scanRoots 2>$null
  if ($LASTEXITCODE -eq 0 -and $matches) {
    Write-Host "BRAND_INTEGRITY_FAIL pattern=$pattern" -ForegroundColor Red
    $matches
    $fail = $true
  }
}

$directLogoImports = rg -n "from .*\.(svg|png|jpg|jpeg|ico|webp)|src=.*(logo|crest|favicon).*\.(svg|png|jpg|jpeg|ico|webp)" frontend/dashboards/src 2>$null
if ($LASTEXITCODE -eq 0 -and $directLogoImports) {
  Write-Host "DIRECT_LOGO_IMPORT_REVIEW_REQUIRED" -ForegroundColor Yellow
  $directLogoImports
}

if ($fail) {
  exit 1
}

Write-Host "BRAND_INTEGRITY_PASS"
exit 0
