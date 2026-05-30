param(
    [string]$StatusFile = "docs/CURRENT_RELEASE_STATUS.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $StatusFile)) {
    Write-Error "status file not found: $StatusFile"
    exit 1
}

$text = Get-Content -Raw -Path $StatusFile

function Get-MatchValue {
    param(
        [string]$Pattern,
        [string]$Label
    )

    $m = [regex]::Match($text, $Pattern)
    if (-not $m.Success) {
        throw "missing required field: $Label"
    }

    return $m.Groups[1].Value.Trim()
}

$decision = Get-MatchValue -Pattern '(?im)^\s*Repository-wide decision:\s*([^\.\r\n]+)' -Label 'repository-wide decision'
$candidateSha = Get-MatchValue -Pattern '(?im)^\s*-\s*Candidate SHA:\s*`([^`]+)`' -Label 'Candidate SHA'
$approvedSha = Get-MatchValue -Pattern '(?im)^\s*-\s*Approved deploy SHA:\s*`([^`]+)`' -Label 'Approved deploy SHA'
$runtimeSha = Get-MatchValue -Pattern '(?im)^\s*-\s*Runtime-validated SHA:\s*`([^`]+)`' -Label 'Runtime-validated SHA'
$parityVerdict = Get-MatchValue -Pattern '(?im)^\s*-\s*Parity verdict:\s*`([^`]+)`' -Label 'Parity verdict'
$protectedSpineVerdict = Get-MatchValue -Pattern '(?im)^\s*-\s*Protected-spine verdict:\s*`([^`]+)`' -Label 'Protected-spine verdict'
$documentedChecksum = Get-MatchValue -Pattern '(?im)^\s*-\s*Status checksum \(SHA256 over decision\+metadata tuple\):\s*`([^`]+)`' -Label 'Status checksum'

$tuple = @(
    $decision,
    $candidateSha,
    $approvedSha,
    $runtimeSha,
    $parityVerdict,
    $protectedSpineVerdict
) -join '|'

$sha256 = [System.Security.Cryptography.SHA256]::Create()
$bytes = [System.Text.Encoding]::UTF8.GetBytes($tuple)
$computedBytes = $sha256.ComputeHash($bytes)
$computedChecksum = ([System.BitConverter]::ToString($computedBytes)).Replace('-', '').ToLowerInvariant()

Write-Output "[canonical-status-metadata] decision=$decision"
Write-Output "[canonical-status-metadata] candidate_sha=$candidateSha approved_sha=$approvedSha runtime_sha=$runtimeSha"
Write-Output "[canonical-status-metadata] parity_verdict=$parityVerdict protected_spine_verdict=$protectedSpineVerdict"
Write-Output "[canonical-status-metadata] documented_checksum=$documentedChecksum"
Write-Output "[canonical-status-metadata] computed_checksum=$computedChecksum"

if ($documentedChecksum -eq 'PENDING') {
    Write-Error "status checksum is still PENDING"
    exit 1
}

if ($documentedChecksum -ne $computedChecksum) {
    Write-Error "status checksum mismatch"
    exit 1
}

Write-Output "OK canonical status metadata check passed"
exit 0
