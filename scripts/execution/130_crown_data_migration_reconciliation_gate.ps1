param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot
. (Join-Path $repoRoot "scripts/execution/modules/runtime_evidence_validation.ps1")

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\data-migration\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\data-migration\latest"
New-Dir $outDir
New-Dir $latestDir

$requiredDomains = @(
    "students",
    "households",
    "guardians",
    "staff",
    "enrollment",
    "attendance",
    "courses",
    "sections",
    "grades",
    "transcripts",
    "billing",
    "payments",
    "financial_aid",
    "communications",
    "documents"
)

$searchRoots = @("backend", "frontend", "scripts", "docs") | ForEach-Object { Join-Path $repoRoot $_ } | Where-Object { Test-Path $_ }
$allFiles = @()
foreach ($root in $searchRoots) {
    $allFiles += Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(py|ps1|js|jsx|ts|tsx|md|csv|json)$" }
}

$rows = @()
foreach ($domain in $requiredDomains) {
    $hits = @($allFiles | Where-Object { $_.Name -match $domain -or ((Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue) -match $domain) })
    $hasImportSignal = @($hits | Where-Object { $_.Name -match "import|migration|seed|reconcile" -or ((Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue) -match "import|migration|reconcile|rollback") }).Count -gt 0
    $rows += [pscustomobject]@{
        Domain = $domain
        FileHitCount = $hits.Count
        ImportOrReconciliationSignal = $hasImportSignal
        CompletionStatus = if ($hasImportSignal) { "PROOF_REQUIRED" } else { "BLOCKED_MISSING_IMPORT_RECONCILIATION_SIGNAL" }
    }
}

$runtime = Read-CrownRuntimeEvidence -Gate "data-migration" -Keys $requiredDomains -Criteria @("rehearsal", "count_reconciliation", "error_reconciliation", "rollback", "tenant_isolation") -OutputDir $outDir
if ($runtime.pass -eq $true) {
    foreach ($row in $rows) {
        if ($row.CompletionStatus -notlike "BLOCKED_*") { $row.CompletionStatus = "PASS" }
    }
}

$errorRows = @($rows | Where-Object { $_.CompletionStatus -ne "PASS" })
$rows | Export-Csv -Path (Join-Path $outDir "10_import_counts.csv") -NoTypeInformation -Encoding UTF8
$errorRows | Export-Csv -Path (Join-Path $outDir "20_reconciliation_errors.csv") -NoTypeInformation -Encoding UTF8

$rollback = @(
    "# CROWN Data Migration Rollback Test",
    "",
    $(if ($runtime.pass -eq $true) { "Validated rollback execution proof: $env:CROWN_RELEASE_RUNTIME_EVIDENCE" } else { "No executable rollback proof was validated." }),
    "A green migration gate requires live import rehearsal, count reconciliation, error reconciliation, rollback execution, and tenant isolation proof."
)
Write-Utf8 -Path (Join-Path $outDir "30_rollback_test.md") -Lines $rollback

$pass = ($runtime.pass -eq $true -and $errorRows.Count -eq 0)
$summary = @(
    "# CROWN Data Migration Reconciliation Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Required domains: $($requiredDomains.Count)",
    "- Non-pass rows: $($errorRows.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This static gate documents migration/reconciliation coverage signals but intentionally does not pass without live rehearsal evidence."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    runtime_evidence_errors = @($runtime.errors)
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    required_domain_count = $requiredDomains.Count
    non_pass_count = $errorRows.Count
    domains = $rows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
