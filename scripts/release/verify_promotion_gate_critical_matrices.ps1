param(
    [string]$CertMatrixScript = "scripts/release/verify_certification_matrices.ps1",
    [string]$CertPolicyScript = "scripts/release/verify_certification_policy_artifacts.ps1",
    [string]$HostedCiScript = "scripts/release/verify_hosted_ci_fail_closed.ps1",
    [string]$ScopeLockScript = "scripts/release/verify_scope_lock_no_net_new.ps1",
    [string]$DeployParityPacket = "docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_153149.json",
    [string]$ProtectedSpinePacket = "docs/release/live-audit/protected-spine/protected_spine_candidate_sha_packet_20260530_113226.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path

foreach ($path in @($CertMatrixScript, $CertPolicyScript, $HostedCiScript, $ScopeLockScript, $DeployParityPacket, $ProtectedSpinePacket)) {
    if (-not (Test-Path -Path $path)) {
        Write-Error "promotion-gate prerequisite missing: $path"
        exit 2
    }
}

pwsh -NoProfile -File $CertMatrixScript
if ($LASTEXITCODE -ne 0) { Write-Error "certification matrices gate failed"; exit 3 }

pwsh -NoProfile -File $CertPolicyScript
if ($LASTEXITCODE -ne 0) { Write-Error "certification policy gate failed"; exit 4 }

pwsh -NoProfile -File $HostedCiScript
if ($LASTEXITCODE -ne 0) { Write-Error "hosted CI fail-closed gate failed"; exit 5 }

pwsh -NoProfile -File $ScopeLockScript
if ($LASTEXITCODE -ne 0) { Write-Error "scope lock / no-net-new gate failed"; exit 6 }

$deploy = Get-Content -Raw -Path $DeployParityPacket | ConvertFrom-Json
if (-not $deploy.evaluation.parity_closed) {
    Write-Error "deploy parity is not closed"
    exit 7
}

$spine = Get-Content -Raw -Path $ProtectedSpinePacket | ConvertFrom-Json
if (-not $spine.overall_pass) {
    Write-Error "protected spine candidate packet is not passing"
    exit 8
}

Write-Output "[promotion-gate-critical] parity_closed=$($deploy.evaluation.parity_closed) protected_spine_overall_pass=$($spine.overall_pass)"
Write-Output "OK promotion gate critical matrices passed"
exit 0
