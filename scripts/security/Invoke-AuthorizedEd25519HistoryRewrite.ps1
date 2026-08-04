[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [string]$WorkRoot = (Join-Path $env:TEMP ('Crown2026-history-rewrite-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))),
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Repository = 'tcmegahan/Crown2026'
$AuthorizedBaseSha = [string]::Concat(@(
    '0c3b402f'
    '1cefe76d'
    'b7d3b641'
    'af3e77c9'
    '2c3578c1'
))
$AuthorizedRunnerPath = 'scripts/security/Invoke-AuthorizedEd25519HistoryRewrite.ps1'
$ForbiddenPath = [string]::Concat(@(
    'solomon_governance_c1/governance/c1/runtime/audit_pack/'
    '20260515T185051Z/crypto_attestation/'
    'ed25519_'
    'private_'
    'key_'
    'DO_NOT_SHARE'
    '.pem'
))

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $previous = Get-Location
    try {
        if ($WorkingDirectory) { Set-Location $WorkingDirectory }
        & $FilePath @ArgumentList
        if ($LASTEXITCODE -ne 0) {
            throw "$FilePath exited with code $LASTEXITCODE"
        }
    }
    finally {
        Set-Location $previous
    }
}

Assert-Command git
Assert-Command gh
Assert-Command python
Assert-Command gitleaks
Assert-Command bash

Invoke-Native gh @('auth', 'status')
Invoke-Native git @('filter-repo', '--version')

$remoteUrl = "https://github.com/$Repository.git"
$observedMain = (& git ls-remote $remoteUrl refs/heads/main).Split("`t")[0]
if ($LASTEXITCODE -ne 0 -or -not $observedMain) { throw 'Unable to resolve remote main.' }

New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
$mirror = Join-Path $WorkRoot 'Crown2026-remediation.git'
$fresh = Join-Path $WorkRoot 'fresh-clone.git'
$evidence = Join-Path $WorkRoot 'evidence'
New-Item -ItemType Directory -Path $evidence -Force | Out-Null

Invoke-Native git @('clone', '--mirror', $remoteUrl, $mirror)
$mirrorMain = (& git -C $mirror rev-parse refs/heads/main).Trim()
if ($mirrorMain -ne $observedMain) {
    throw "Mirror identity mismatch. Remote advertised $observedMain but mirror resolved $mirrorMain."
}

$mainParents = @(& git -C $mirror rev-list --parents -n 1 refs/heads/main)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect authoritative main ancestry.' }
$parentParts = $mainParents[0] -split ' '
if ($parentParts.Count -ne 2) {
    throw 'Authorized runner commit must have exactly one parent.'
}
if ($parentParts[1] -ne $AuthorizedBaseSha) {
    throw "Unauthorized main ancestry. Expected $AuthorizedBaseSha but observed $($parentParts[1])."
}

$authorizedDelta = @(& git -C $mirror diff --name-only $AuthorizedBaseSha refs/heads/main)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect authorized main delta.' }
if ($authorizedDelta.Count -ne 1 -or $authorizedDelta[0] -ne $AuthorizedRunnerPath) {
    throw "Unauthorized main delta. Expected only $AuthorizedRunnerPath."
}

& git -C $mirror for-each-ref '--format=%(refname) %(objectname)' refs/heads refs/tags |
    Sort-Object | Set-Content -Encoding utf8 (Join-Path $evidence 'refs-before.txt')

Invoke-Native git @('-C', $mirror, 'bundle', 'create', (Join-Path $evidence 'preservation-before.bundle'), '--branches', '--tags')
Get-FileHash (Join-Path $evidence 'preservation-before.bundle') -Algorithm SHA256 |
    Format-List | Out-File -Encoding utf8 (Join-Path $evidence 'preservation-before.bundle.sha256.txt')

Invoke-Native git @('-C', $mirror, 'filter-repo', '--path', $ForbiddenPath, '--invert-paths', '--force')

$verifier = Join-Path $PSScriptRoot '..\..\tools\verify_remediated_git_bundle.sh'
if (-not (Test-Path $verifier)) {
    throw "Verifier not found at $verifier"
}

Invoke-Native bash @($verifier, '--repo', $mirror, '--forbidden-path', $ForbiddenPath)
Invoke-Native git @('-C', $mirror, 'fsck', '--full', '--strict')

$gitleaksReport = Join-Path $evidence 'gitleaks-before-push.json'
Invoke-Native gitleaks @('detect', '--source', $mirror, '--no-banner', '--redact', '--log-opts=--all', '--report-format', 'json', '--report-path', $gitleaksReport)
$findings = Get-Content $gitleaksReport -Raw | ConvertFrom-Json
if (@($findings).Count -ne 0) {
    throw "Gitleaks reported $(@($findings).Count) findings after rewrite."
}

$bundle = Join-Path $evidence 'Crown2026-remediated.bundle'
Invoke-Native git @('-C', $mirror, 'bundle', 'create', $bundle, '--branches', '--tags')
Invoke-Native bash @($verifier, '--bundle', $bundle, '--forbidden-path', $ForbiddenPath)
Get-FileHash $bundle -Algorithm SHA256 |
    Format-List | Out-File -Encoding utf8 (Join-Path $evidence 'Crown2026-remediated.bundle.sha256.txt')

& git -C $mirror for-each-ref '--format=%(refname) %(objectname)' refs/heads refs/tags |
    Sort-Object | Set-Content -Encoding utf8 (Join-Path $evidence 'refs-after.txt')

$beforeNames = Get-Content (Join-Path $evidence 'refs-before.txt') | ForEach-Object { ($_ -split ' ')[0] }
$afterNames = Get-Content (Join-Path $evidence 'refs-after.txt') | ForEach-Object { ($_ -split ' ')[0] }
if (Compare-Object $beforeNames $afterNames) {
    throw 'Retained branch/tag namespace changed during rewrite.'
}

$rewrittenMain = (& git -C $mirror rev-parse refs/heads/main).Trim()
@(
    "authorized_base=$AuthorizedBaseSha"
    "source_main=$observedMain"
    "rewritten_main=$rewrittenMain"
    "forbidden_path=$ForbiddenPath"
    "prepared_at=$([DateTime]::UtcNow.ToString('o'))"
) | Set-Content -Encoding utf8 (Join-Path $evidence 'rewrite-summary.txt')

if (-not $Execute) {
    Write-Host 'Verification completed. No remote refs were changed.'
    Write-Host "Rewritten main: $rewrittenMain"
    Write-Host "Evidence: $evidence"
    Write-Host 'Re-run with -Execute to perform the authorized atomic ref update.'
    exit 0
}

$remoteMainBeforePush = (& git ls-remote $remoteUrl refs/heads/main).Split("`t")[0]
if ($remoteMainBeforePush -ne $observedMain) {
    throw "Remote main drifted before push. Expected $observedMain but observed $remoteMainBeforePush."
}

$refspecs = & git -C $mirror for-each-ref '--format=+%(objectname):%(refname)' refs/heads refs/tags
if (-not $refspecs) { throw 'No retained refs found for promotion.' }

if ($PSCmdlet.ShouldProcess($Repository, 'Atomically force-update retained branches and tags to rewritten history')) {
    Invoke-Native git (@('-C', $mirror, 'push', '--atomic', $remoteUrl) + $refspecs)
}
else {
    throw 'Remote update was not confirmed.'
}

Invoke-Native git @('clone', '--mirror', $remoteUrl, $fresh)
Invoke-Native bash @($verifier, '--repo', $fresh, '--forbidden-path', $ForbiddenPath)
Invoke-Native git @('-C', $fresh, 'fsck', '--full', '--strict')

$postReport = Join-Path $evidence 'gitleaks-after-push.json'
Invoke-Native gitleaks @('detect', '--source', $fresh, '--no-banner', '--redact', '--log-opts=--all', '--report-format', 'json', '--report-path', $postReport)
$postFindings = Get-Content $postReport -Raw | ConvertFrom-Json
if (@($postFindings).Count -ne 0) {
    throw "Post-push Gitleaks reported $(@($postFindings).Count) findings."
}

$authoritativeMain = (& git -C $fresh rev-parse refs/heads/main).Trim()
if ($authoritativeMain -ne $rewrittenMain) {
    throw "Post-push main mismatch. Expected $rewrittenMain but observed $authoritativeMain."
}

@(
    'result=PASS'
    "authorized_base=$AuthorizedBaseSha"
    "source_main=$observedMain"
    "authoritative_rewritten_main=$authoritativeMain"
    "verified_at=$([DateTime]::UtcNow.ToString('o'))"
) | Set-Content -Encoding utf8 (Join-Path $evidence 'authoritative-result.txt')

Write-Host 'Authoritative history rewrite completed and verified.'
Write-Host "New main: $authoritativeMain"
Write-Host "Evidence: $evidence"
