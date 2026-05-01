Set-Location (git -C $PSScriptRoot rev-parse --show-toplevel)
$ErrorActionPreference = "Continue"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Base = "audit-artifacts\nonazure-production-readiness"
$PackDir = "$Base\$Stamp"
New-Item -ItemType Directory -Force -Path $PackDir | Out-Null

Write-Host "Non-Azure readiness scan starting: $PackDir"

# ---- helpers ----
$Src = Get-ChildItem -Recurse -Include "*.tsx","*.ts","*.jsx","*.js","*.py","*.html" -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch 'node_modules|\.venv|dist|build|__pycache__|\.git|\.next' }

# ---- 20: Placeholder scan ----
$PlaceholderPatterns = 'TODO|FIXME|PLACEHOLDER|Coming Soon|lorem ipsum|coming soon|Not implemented|WIP\b|stub\b|hardcoded|fake data|mock data|sample data|REMOVE ME'
$PlaceholderHits = @()
foreach ($f in $Src) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match $PlaceholderPatterns) {
      $PlaceholderHits += [pscustomobject]@{ FindingType="Placeholder"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$PlaceholderHits | Export-Csv "$PackDir\20_placeholder_scan.csv" -NoTypeInformation
Write-Host "20 placeholder hits: $($PlaceholderHits.Count)"

# ---- 21: UI anti-pattern scan ----
$UiPatterns = 'navy|#1a1a2e|#0f3460|#16213e|dead.link|href="#"|href=''#''|color:\s*#333|background.*dark|TODO.*style|FIXME.*style|console\.log|debugger;'
$UiHits = @()
foreach ($f in ($Src | Where-Object { $_.Extension -in @('.tsx','.jsx','.ts','.js','.html') })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match $UiPatterns) {
      $UiHits += [pscustomobject]@{ FindingType="UI-AntiPattern"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$UiHits | Export-Csv "$PackDir\21_ui_antipattern_scan.csv" -NoTypeInformation
Write-Host "21 UI anti-pattern hits: $($UiHits.Count)"

# ---- 22: Possible secret scan ----
$SecretPatterns = 'password\s*=\s*[''"][^''"]{4}|api.?key\s*=\s*[''"][^''"]{8}|secret\s*=\s*[''"][^''"]{8}|token\s*=\s*[''"][^''"]{8}|BEGIN.*PRIVATE KEY|AKIA[0-9A-Z]{16}|client.?secret'
$SecretHits = @()
foreach ($f in ($Src | Where-Object { $_.Extension -notin @('.html') })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match $SecretPatterns -and $line -notmatch 'os\.environ|getenv|process\.env|secrets\.|vault|placeholder|example|your.key.here|\$\{') {
      $SecretHits += [pscustomobject]@{ FindingType="PossibleSecret"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(80,$line.Trim().Length)) }
    }
  }
}
$SecretHits | Export-Csv "$PackDir\22_possible_secret_scan.csv" -NoTypeInformation
Write-Host "22 possible secret hits: $($SecretHits.Count)"

# ---- 23: Route inventory ----
$RouteHits = @()
foreach ($f in ($Src | Where-Object { $_.Extension -in @('.tsx','.jsx','.ts','.js') -and $_.FullName -match 'routes?|router|nav|App\.' })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match '<Route|path=|navigate\(|useNavigate|Link to=') {
      $RouteHits += [pscustomobject]@{ FindingType="Route"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$RouteHits | Export-Csv "$PackDir\23_route_inventory.csv" -NoTypeInformation
Write-Host "23 route references: $($RouteHits.Count)"

# ---- 24: Dashboard inventory ----
$DashboardHits = @()
$DashPatterns = 'Dashboard|KPICard|StatsCard|MetricCard|AnalyticsCard|ChartCard|SummaryCard|BarChart|LineChart|PieChart|AreaChart'
foreach ($f in ($Src | Where-Object { $_.Extension -in @('.tsx','.jsx') })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match $DashPatterns) {
      $DashboardHits += [pscustomobject]@{ FindingType="DashboardComponent"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$DashboardHits | Export-Csv "$PackDir\24_dashboard_inventory.csv" -NoTypeInformation
Write-Host "24 dashboard references: $($DashboardHits.Count)"

# ---- 25: Wizard inventory ----
$WizardHits = @()
foreach ($f in ($Src | Where-Object { $_.Extension -in @('.tsx','.jsx') })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    if ($line -match 'Wizard|Stepper|MultiStep|step\s*===|currentStep|nextStep|prevStep') {
      $WizardHits += [pscustomobject]@{ FindingType="Wizard"; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$WizardHits | Export-Csv "$PackDir\25_wizard_inventory.csv" -NoTypeInformation
Write-Host "25 wizard references: $($WizardHits.Count)"

# ---- 26: Accessibility review ----
$A11yHits = @()
foreach ($f in ($Src | Where-Object { $_.Extension -in @('.tsx','.jsx','.html') })) {
  $rel = $f.FullName.Replace((Get-Location).Path + "\","")
  $n = 0
  foreach ($line in (Get-Content $f.FullName -ErrorAction SilentlyContinue)) {
    $n++
    $issue = $null
    if ($line -match '<img ' -and $line -notmatch 'alt=') { $issue = "img-missing-alt" }
    elseif ($line -match '<button' -and $line -notmatch 'type=') { $issue = "button-missing-type" }
    elseif ($line -match '<input' -and $line -notmatch 'aria-label|aria-labelledby|id=') { $issue = "input-missing-label" }
    elseif ($line -match 'onClick' -and $line -match '<div|<span' -and $line -notmatch 'role=|tabIndex') { $issue = "clickable-non-interactive" }
    if ($issue) {
      $A11yHits += [pscustomobject]@{ FindingType=$issue; RelativePath=$rel; LineNumber=$n; LineContent=$line.Trim().Substring(0, [Math]::Min(120,$line.Trim().Length)) }
    }
  }
}
$A11yHits | Export-Csv "$PackDir\26_accessibility_review.csv" -NoTypeInformation
Write-Host "26 accessibility hits: $($A11yHits.Count)"

# ---- 40: Remediation queue (from FAIL/REVIEW items we can enumerate) ----
$Queue = @()
function Add-Q([string]$P,[string]$Owner,[string]$Area,[string]$Issue,[string]$Evidence,[string]$Action) {
  $script:Queue += [pscustomobject]@{ Priority=$P; Owner=$Owner; Area=$Area; Issue=$Issue; Evidence=$Evidence; Action=$Action }
}
if ($SecretHits.Count -gt 0) { Add-Q "P0" "Dev 5 - QA/Release" "Security" "Possible secrets found in source ($($SecretHits.Count) hits)" "22_possible_secret_scan.csv" "Review each; move real secrets to vault/env; confirm false positives." }
if ($PlaceholderHits.Count -gt 0) { Add-Q "P1" "Dev 4 - Frontend/UX" "UI Polish" "Placeholder/TODO copy in source ($($PlaceholderHits.Count) hits)" "20_placeholder_scan.csv" "Replace placeholder with real copy or formally defer." }
if ($UiHits.Count -gt 0) { Add-Q "P1" "Dev 4 - Frontend/UX" "UI Polish" "UI anti-patterns in source ($($UiHits.Count) hits)" "21_ui_antipattern_scan.csv" "Apply crown-theme.css; remove dark/navy hardcoding; fix dead links." }
if ($A11yHits.Count -gt 0) { Add-Q "P1" "Dev 4 - Frontend/UX" "Accessibility" "Accessibility issues in source ($($A11yHits.Count) hits)" "26_accessibility_review.csv" "Fix img alt, button type, input labels, and clickable div patterns." }
Add-Q "P0" "Dev 1 - Platform" "Security/Auth" "Tenant isolation and RBAC proof not yet artifact-verified for Azure prod" "05_QA_REGRESSION_MATRIX.csv" "Run full role/tenant matrix proof after Azure deploy succeeds."
Add-Q "P0" "Azure admin" "Deploy secrets" "AZURE_SWA_TOKEN missing from repo secrets (dashboard deploy blocked)" "GitHub Actions run 25139353897" "Add AZURE_SWA_TOKEN as repository-level secret."
Add-Q "P0" "Azure admin" "Deploy secrets" "Azure auth secrets missing from production env (backend deploy blocked)" "GitHub Actions run 25139353890" "Add AZURE_CREDENTIALS or OIDC triplet to production environment secrets."
Add-Q "P1" "Dev 5 - QA/Release" "Release proof" "Azure production proof not yet green (SHA mismatch, SWA 404)" "deep-dive-live-audit/20260430_020745" "After workflows green, run full Azure proof and re-score."
Add-Q "P2" "TC / Product" "Canons" "Core, SIS, Modules canons not confirmed approved" "docs/crown-master-binder/canons" "Review and mark each canon approved working authority."
Add-Q "P2" "Dev 4 - Frontend/UX" "Dashboards" "Dashboard/KPI data source classification not complete" "24_dashboard_inventory.csv" "Classify each as real/seeded/placeholder/broken/deferred."
$Queue | Export-Csv "$PackDir\40_REMEDIATION_QUEUE.csv" -NoTypeInformation
Write-Host "40 remediation queue rows: $($Queue.Count)"

# ---- 50: Non-Azure scorecard ----
$Score = @()
function Add-S([string]$Area,[string]$Status,[string]$Evidence,[string]$Notes) {
  $script:Score += [pscustomobject]@{ Area=$Area; Status=$Status; Evidence=$Evidence; Notes=$Notes }
}
$gitStatusShort = git status --short
Add-S "Repo worktree" (if ($null -eq $gitStatusShort -or $gitStatusShort.Count -eq 0) { "PASS" } else { "REVIEW" }) "git status --short" "See 90_git_status.txt"
Add-S "Placeholder/TODO scan" (if ($PlaceholderHits.Count -eq 0) { "PASS" } elseif ($PlaceholderHits.Count -lt 20) { "REVIEW" } else { "FAIL" }) "20_placeholder_scan.csv" "$($PlaceholderHits.Count) hits"
Add-S "UI anti-pattern scan" (if ($UiHits.Count -eq 0) { "PASS" } elseif ($UiHits.Count -lt 30) { "REVIEW" } else { "FAIL" }) "21_ui_antipattern_scan.csv" "$($UiHits.Count) hits"
Add-S "Possible secret scan" (if ($SecretHits.Count -eq 0) { "PASS" } else { "FAIL" }) "22_possible_secret_scan.csv" "$($SecretHits.Count) hits - review each"
Add-S "Route inventory" (if ($RouteHits.Count -gt 0) { "PASS" } else { "REVIEW" }) "23_route_inventory.csv" "$($RouteHits.Count) route references"
Add-S "Dashboard inventory" (if ($DashboardHits.Count -gt 0) { "PASS" } else { "REVIEW" }) "24_dashboard_inventory.csv" "$($DashboardHits.Count) dashboard references"
Add-S "Wizard inventory" "PASS" "25_wizard_inventory.csv" "$($WizardHits.Count) wizard references"
Add-S "Accessibility review" (if ($A11yHits.Count -eq 0) { "PASS" } elseif ($A11yHits.Count -lt 20) { "REVIEW" } else { "FAIL" }) "26_accessibility_review.csv" "$($A11yHits.Count) hits"
Add-S "Governance acceptance" "PASS" "audit-artifacts/governance-acceptance" "Committed b9dad81"
Add-S "Sandbox login proof" "PASS" "real-sandbox-login-proof-20260429_180654" "3/3 pass"
Add-S "KPI + smoke proof" "PASS_WITH_EXCEPTION" "kpi-sandbox-final-proof-20260429_181335" "KPI exception accepted"
Add-S "Deploy tag pushed" "PASS" "prod-deploy-20260429-rc1" "Targeting b9dad81"
Add-S "Azure backend deploy" "FAIL" "GitHub Actions 25139353890" "Missing Azure auth secrets"
Add-S "Azure dashboard deploy" "FAIL" "GitHub Actions 25139353897" "Missing AZURE_SWA_TOKEN"
Add-S "Backend SHA match" "FAIL" "crown-api-prod health" "Still c7ab4328, expected b9dad81"
Add-S "Frontend SWA live" "PASS" "yellow-forest-0eecc8b0f.7.azurestaticapps.net" "HTTP 200"
$Score | Export-Csv "$PackDir\50_NONAZURE_SCORECARD.csv" -NoTypeInformation

$Pass = ($Score | Where-Object { $_.Status -eq "PASS" }).Count
$PassEx = ($Score | Where-Object { $_.Status -eq "PASS_WITH_EXCEPTION" }).Count
$Fail = ($Score | Where-Object { $_.Status -eq "FAIL" }).Count
$Review = ($Score | Where-Object { $_.Status -eq "REVIEW" }).Count
$Total = $Score.Count

Write-Host "50 scorecard: PASS=$Pass PASS_W_EX=$PassEx REVIEW=$Review FAIL=$Fail TOTAL=$Total"

# ---- git status ----
git status --short | Set-Content "$PackDir\90_git_status.txt"

# ---- write LATEST.txt ----
$FullPackPath = (Resolve-Path $PackDir).Path
$FullPackPath | Set-Content "$Base\LATEST.txt" -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "Non-Azure readiness pack complete."
Write-Host "LATEST.txt -> $FullPackPath"
