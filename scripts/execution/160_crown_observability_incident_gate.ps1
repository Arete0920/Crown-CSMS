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
$outDir = Join-Path $repoRoot ".crown-audit\observability\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\observability\latest"
New-Dir $outDir
New-Dir $latestDir

$monitoringControls = @(
    "frontend_backend_database_health_monitoring",
    "backend_frontend_error_monitoring",
    "failed_login_and_privileged_access_monitoring",
    "payment_webhook_monitoring",
    "email_sms_delivery_monitoring",
    "api_latency_monitoring",
    "backup_failure_monitoring",
    "audit_log_monitoring",
    "tenant_isolation_anomaly_monitoring",
    "on_call_escalation_process"
)

$incidentControls = @(
    "severity_matrix",
    "cross_tenant_critical_classification",
    "customer_notification_workflow",
    "evidence_preservation_procedure",
    "containment_procedure",
    "root_cause_template",
    "corrective_action_process",
    "incident_tabletop_or_test",
    "break_glass_access_review",
    "contact_roster"
)

$runtime = Read-CrownRuntimeEvidence -Gate "observability" -Keys @($monitoringControls + $incidentControls) -Criteria @("executed_control") -OutputDir $outDir

$monitorRows = foreach ($control in $monitoringControls) {
    [pscustomobject]@{ Control = $control; RuntimeEvidence = if ($runtime.pass -eq $true) { $env:CROWN_RELEASE_RUNTIME_EVIDENCE } else { "missing or invalid" }; CompletionStatus = if ($runtime.pass -eq $true) { "PASS" } else { "BLOCKED_NO_RUNTIME_MONITORING_EVIDENCE" } }
}
$incidentRows = foreach ($control in $incidentControls) {
    [pscustomobject]@{ Control = $control; RuntimeEvidence = if ($runtime.pass -eq $true) { $env:CROWN_RELEASE_RUNTIME_EVIDENCE } else { "missing or invalid" }; CompletionStatus = if ($runtime.pass -eq $true) { "PASS" } else { "BLOCKED_NO_INCIDENT_TEST_EVIDENCE" } }
}

$monitorRows | Export-Csv -Path (Join-Path $outDir "10_monitoring_controls.csv") -NoTypeInformation -Encoding UTF8
$incidentRows | Export-Csv -Path (Join-Path $outDir "20_incident_response_controls.csv") -NoTypeInformation -Encoding UTF8
Write-Utf8 -Path (Join-Path $outDir "30_tabletop_or_test.md") -Lines @(
    "# CROWN Incident Tabletop / Test Evidence",
    "",
    $(if ($runtime.pass -eq $true) { "Validated incident exercise proof: $env:CROWN_RELEASE_RUNTIME_EVIDENCE" } else { "No incident exercise proof was validated." }),
    "A green result requires executed tabletop/test evidence and current contact/escalation proof."
)

$pass = ($runtime.pass -eq $true)
$summary = @(
    "# CROWN Observability and Incident Readiness Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Monitoring controls: $($monitoringControls.Count)",
    "- Incident controls: $($incidentControls.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This gate intentionally fails until live monitoring and incident-response evidence are attached."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    runtime_evidence_errors = @($runtime.errors)
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    monitoring_control_count = $monitoringControls.Count
    incident_control_count = $incidentControls.Count
    monitoring_controls = $monitorRows
    incident_controls = $incidentRows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
