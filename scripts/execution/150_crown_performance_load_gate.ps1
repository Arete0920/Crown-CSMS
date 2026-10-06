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
$outDir = Join-Path $repoRoot ".crown-audit\performance\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\performance\latest"
New-Dir $outDir
New-Dir $latestDir

$scenarios = @(
    "morning_attendance_submission",
    "parent_portal_login_surge",
    "gradebook_save_storm",
    "billing_invoice_run",
    "report_card_generation",
    "large_student_import",
    "communications_blast",
    "role_dashboard_load",
    "multi_tenant_concurrent_use",
    "payment_webhook_burst"
)

$runtime = Read-CrownRuntimeEvidence -Gate "performance" -Keys $scenarios -Criteria @("load_test") -OutputDir $outDir
$rows = @()
foreach ($scenario in $scenarios) {
    $proof = @($runtime.records | Where-Object { $_.key -eq $scenario })
    $rows += [pscustomobject]@{
        Scenario = $scenario
        TargetUsers = if ($runtime.pass -eq $true) { $proof[0].accepted_targets.users } else { "TBD" }
        TargetP95Ms = if ($runtime.pass -eq $true) { $proof[0].accepted_targets.p95_ms } else { "TBD" }
        TargetErrorRate = if ($runtime.pass -eq $true) { $proof[0].accepted_targets.error_rate } else { "TBD" }
        RuntimeEvidence = if ($runtime.pass -eq $true) { $env:CROWN_RELEASE_RUNTIME_EVIDENCE } else { "missing or invalid" }
        CompletionStatus = if ($runtime.pass -eq $true) { "PASS" } else { "BLOCKED_NO_LOAD_TEST_EVIDENCE" }
    }
}

$failures = @($rows | Where-Object { $_.CompletionStatus -ne "PASS" })
$rows | Export-Csv -Path (Join-Path $outDir "10_scenarios.csv") -NoTypeInformation -Encoding UTF8
$failures | Export-Csv -Path (Join-Path $outDir "20_failures.csv") -NoTypeInformation -Encoding UTF8

$pass = ($runtime.pass -eq $true -and $failures.Count -eq 0)
$summary = @(
    "# CROWN Performance and Load Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Scenarios: $($scenarios.Count)",
    "- Non-pass rows: $($failures.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This gate intentionally fails until performance/load tests are executed against a runtime environment and evidence is attached."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    runtime_evidence_errors = @($runtime.errors)
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    scenario_count = $scenarios.Count
    non_pass_count = $failures.Count
    scenarios = $rows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
