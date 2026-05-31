param(
    [string]$HostedCiSnapshot = "docs/release/live-audit/hosted-ci/hosted_ci_candidate_20260530_113145.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $HostedCiSnapshot)) {
    Write-Error "hosted CI snapshot missing: $HostedCiSnapshot"
    exit 2
}

$data = Get-Content -Raw -Path $HostedCiSnapshot | ConvertFrom-Json
if ($null -eq $data.candidate_sha -or [string]::IsNullOrWhiteSpace([string]$data.candidate_sha)) {
    Write-Error "fail-closed: candidate_sha missing in hosted CI snapshot"
    exit 3
}

$candidateRuns = @($data.runs)
$success = @($candidateRuns | Where-Object { $_.conclusion -eq "success" }).Count
$failed = @($candidateRuns | Where-Object { $_.conclusion -eq "failure" }).Count

Write-Output "[hosted-ci-fail-closed] candidate_sha=$($data.candidate_sha) runs=$($candidateRuns.Count) success=$success failed=$failed"

if ($candidateRuns.Count -lt 1) {
    Write-Error "fail-closed: no hosted CI runs bound to candidate SHA"
    exit 4
}

if ($success -lt 1) {
    Write-Error "fail-closed: no passing hosted CI run bound to candidate SHA"
    exit 5
}

Write-Output "OK hosted CI fail-closed check passed"
exit 0
