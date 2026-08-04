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
    'b78e36fc'
    '1b5d5f4e'
    'c2302831'
    '913757e8'
    'c2b23142'
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

# Exact SHA-256 hashes of the 24 candidate values observed in the source-locked
# rewritten history. Values are intentionally not stored. The set was derived
# from Gitleaks 8.30.1 at authoritative main b78e36fc... and separately reviewed.
# The three opaque candidates were verified as inert dashboard widget slugs.
$ApprovedCandidateHashChunks = @(
    @('01907e11','fd696a1e','5bebe032','9221dc5c','0fc6525e','2cdc46a8','6f66d708','9ba9f9e4'),
    @('034d630a','83014577','1433ac72','ab20d75c','5a903966','54d15c1f','74e0f98f','2153cdf8'),
    @('0bd7ee7b','d6a86fa4','562930ed','f08336a2','4e2b8890','f2af1e24','3443ebc1','87b2b80b'),
    @('365e9e41','11450392','6daabb90','6e2653ff','78b7cce4','75fbf7f7','e5c2100b','9f2876e7'),
    @('3e8c7c25','c53af0e4','28f44adb','1775afec','c8208c9c','128a3098','3a2078e1','8079c233'),
    @('41c76726','6fa5c53e','234ba342','bcc60327','05d3e6ce','99febf93','534ec028','7cc978d5'),
    @('497f476b','1f6d0947','dfcdf571','6c3d60a8','504b4be9','65ac5d53','14763a83','d942c2d6'),
    @('56ee6815','5bd371bd','972d96d8','d0ef880d','2d0359f1','3e0f0327','bb5ebf94','b4fa7ed6'),
    @('644d0c3b','82bfe5e0','665a116b','2eb139d6','abd6c908','3ede0891','237b1723','e0010a14'),
    @('7077786d','adbb5e2d','f0cbc0af','e3e3bc0d','cc84f9b6','280d70f5','6e79e7bc','8766d3ec'),
    @('94ed1644','4a0fb498','9a806f19','6680caad','0b54418f','b3526522','052cf050','74e7239e'),
    @('96c0a849','c2810b43','37e5182f','fb9e5dc4','579e72b0','a329e8aa','9c7ea8c6','926fa74b'),
    @('9a11cf81','2cb05d44','9411d665','45d969dd','df2c86f4','84b5c5a9','35900bbc','1fd1fe7e'),
    @('9ae33814','e39642b3','7c8a0ca4','8f2badbe','cdcc9a86','a20e847d','0f52f513','9ec0ea55'),
    @('9fd52b76','eb4f5b14','96665b5e','bb116565','2204084e','b614669f','8f4082bd','b962b69e'),
    @('a1e3545e','2f526ae8','9106eb5d','0ec09fe8','16bda1f4','cd1c96da','94c671a3','d30d3e9a'),
    @('a22c78c4','41c5693b','405c5488','6b7c50d4','e267ff75','bd4384d6','eeedcf49','a676250a'),
    @('bd67be1f','63382068','023b1f14','07818e0e','1d6b7c20','18e37205','cf1787fe','a67480e3'),
    @('ce926de9','ba94272b','d7cf3d64','8fb6ce18','d6a44463','ba9bc6e7','59f611cb','ebf685ec'),
    @('ce959c43','4b310a25','b10305af','21c4c539','fedc3a24','316ceaab','76cf6969','25c364d5'),
    @('e1466187','c844c921','b622aff2','197444cf','dc2c8748','9f7a6e71','cef47b31','a1602ced'),
    @('eda13789','0e6044b3','fa083c64','b8696ffb','6a356185','42c3ee7d','7912869e','8e74c9d3'),
    @('ee659225','11bc1457','eb196ebc','b2643d29','27febaa6','147f54ae','56ac88a2','3b2c9bc3'),
    @('fb9690e1','4273a10f','39f2281a','c64c4181','f3f10758','b9692133','a3cc8b3c','db448118')
)
$ApprovedCandidateHashes = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($chunks in $ApprovedCandidateHashChunks) {
    [void]$ApprovedCandidateHashes.Add(($chunks -join ''))
}
if ($ApprovedCandidateHashes.Count -ne 24) {
    throw "Approved candidate hash manifest is malformed: expected 24 unique hashes, observed $($ApprovedCandidateHashes.Count)."
}

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

function Get-StringSha256 {
    param([Parameter(Mandatory)][string]$Value)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    $digest = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($digest).ToLowerInvariant()
}

function Invoke-GitleaksAdjudicated {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$ReportPath,
        [Parameter(Mandatory)][string]$Stage
    )

    $rawReport = "$ReportPath.raw.json"
    try {
        & gitleaks detect --source $Source --no-banner '--log-opts=--all' --report-format json --report-path $rawReport
        $scanExit = $LASTEXITCODE
        if ($scanExit -notin @(0, 1)) {
            throw "Gitleaks failed during $Stage with exit code $scanExit."
        }
        if (-not (Test-Path -LiteralPath $rawReport)) {
            throw "Gitleaks did not create the expected report during $Stage."
        }

        $raw = Get-Content -LiteralPath $rawReport -Raw
        $findings = if ([string]::IsNullOrWhiteSpace($raw)) { @() } else { @($raw | ConvertFrom-Json) }
        $safeFindings = [System.Collections.Generic.List[object]]::new()
        $unmatched = [System.Collections.Generic.List[object]]::new()
        $observedHashes = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        foreach ($finding in $findings) {
            $candidate = [string]$finding.Secret
            if ([string]::IsNullOrEmpty($candidate)) {
                $candidate = [string]$finding.Match
            }
            if ([string]::IsNullOrEmpty($candidate)) {
                throw "Gitleaks finding lacks a candidate value during $Stage."
            }

            $candidateHash = Get-StringSha256 -Value $candidate
            [void]$observedHashes.Add($candidateHash)
            $safe = [pscustomobject]@{
                RuleID = [string]$finding.RuleID
                Description = [string]$finding.Description
                File = [string]$finding.File
                StartLine = [int]$finding.StartLine
                EndLine = [int]$finding.EndLine
                Commit = [string]$finding.Commit
                Fingerprint = [string]$finding.Fingerprint
                CandidateSha256 = $candidateHash
            }
            $safeFindings.Add($safe)
            if (-not $ApprovedCandidateHashes.Contains($candidateHash)) {
                $unmatched.Add($safe)
            }
        }

        $missingHashes = @($ApprovedCandidateHashes | Where-Object { -not $observedHashes.Contains($_) })
        if ($unmatched.Count -ne 0 -or $missingHashes.Count -ne 0) {
            $safeReport = [System.IO.Path]::ChangeExtension($ReportPath, '.unmatched-metadata.json')
            [pscustomobject]@{
                Stage = $Stage
                FindingCount = $findings.Count
                ObservedUniqueCandidateCount = $observedHashes.Count
                UnmatchedFindings = @($unmatched)
                MissingApprovedCandidateHashes = $missingHashes
            } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $safeReport -Encoding utf8
            throw "Candidate-hash adjudication failed during $Stage: unmatched=$($unmatched.Count), missing=$($missingHashes.Count). Safe metadata: $safeReport"
        }

        @($safeFindings) | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReportPath -Encoding utf8
        Write-Host "Gitleaks $Stage PASS: $($findings.Count) findings resolved to exactly $($observedHashes.Count) source-locked approved candidates."
    }
    finally {
        if (Test-Path -LiteralPath $rawReport) {
            Remove-Item -LiteralPath $rawReport -Force
        }
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
Invoke-GitleaksAdjudicated -Source $mirror -ReportPath $gitleaksReport -Stage 'before-push'

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
    "approved_candidate_hashes=$($ApprovedCandidateHashes.Count)"
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
Invoke-GitleaksAdjudicated -Source $fresh -ReportPath $postReport -Stage 'after-push'

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
