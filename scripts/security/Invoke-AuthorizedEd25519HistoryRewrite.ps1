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
    '0a03e825'
    '2febe8da'
    'ec7ff819'
    '570fde98'
    'bacd70b5'
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

function Invoke-GitleaksAdjudicated {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$ReportPath,
        [Parameter(Mandatory)][string]$ApprovedIgnorePath,
        [Parameter(Mandatory)][string]$Stage
    )

    if (-not (Test-Path -LiteralPath $ApprovedIgnorePath)) {
        throw "Approved Gitleaks adjudication file not found: $ApprovedIgnorePath"
    }

    & gitleaks detect --source $Source --no-banner --redact '--log-opts=--all' --report-format json --report-path $ReportPath
    $scanExit = $LASTEXITCODE
    if ($scanExit -notin @(0, 1)) {
        throw "Gitleaks failed during $Stage with exit code $scanExit."
    }
    if (-not (Test-Path -LiteralPath $ReportPath)) {
        throw "Gitleaks did not create the expected report during $Stage."
    }

    $raw = Get-Content -LiteralPath $ReportPath -Raw
    $findings = if ([string]::IsNullOrWhiteSpace($raw)) { @() } else { @($raw | ConvertFrom-Json) }

    $approvedSuffixes = @(
        Get-Content -LiteralPath $ApprovedIgnorePath |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and -not $_.StartsWith('#') } |
            ForEach-Object {
                if ($_ -match '^[0-9a-f]{40}:(.+:[^:]+:[0-9]+)$') {
                    $Matches[1]
                }
                elseif ($_ -match '^(.+:[^:]+:[0-9]+)$') {
                    $Matches[1]
                }
            } |
            Where-Object { $_ } |
            Sort-Object -Unique
    )
    if ($approvedSuffixes.Count -eq 0) {
        throw 'Approved Gitleaks adjudication set is empty.'
    }

    $unmatched = @(
        foreach ($finding in $findings) {
            $fingerprint = [string]$finding.Fingerprint
            if ($fingerprint -notmatch '^[0-9a-f]{40}:(.+)$') {
                $finding
                continue
            }
            $stableSuffix = $Matches[1]
            if ($stableSuffix -notin $approvedSuffixes) {
                $finding
            }
        }
    )

    if ($unmatched.Count -ne 0) {
        $safeReport = [System.IO.Path]::ChangeExtension($ReportPath, '.unmatched-metadata.json')
        $unmatched |
            Select-Object RuleID, Description, File, StartLine, EndLine, Commit, Fingerprint |
            ConvertTo-Json -Depth 4 |
            Set-Content -LiteralPath $safeReport -Encoding utf8
        throw "Gitleaks reported $($unmatched.Count) unadjudicated findings during $Stage. Safe metadata: $safeReport"
    }

    Write-Host "Gitleaks $Stage PASS: $($findings.Count) findings matched the source-locked approved adjudication set."
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

$approvedIgnore = Join-Path $PSScriptRoot '..\..\.gitleaksignore'
if (-not (Test-Path -LiteralPath $approvedIgnore)) {
    throw "Approved Gitleaks adjudication file not found at $approvedIgnore"
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
Invoke-GitleaksAdjudicated -Source $mirror -ReportPath $gitleaksReport -ApprovedIgnorePath $approvedIgnore -Stage 'before-push'

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
Invoke-GitleaksAdjudicated -Source $fresh -ReportPath $postReport -ApprovedIgnorePath $approvedIgnore -Stage 'after-push'

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