param(
    [string]$PassCriteria = "docs/release/CERTIFICATION_PASS_CRITERIA_20260530.md",
    [string]$FailCriteria = "docs/release/CERTIFICATION_FAIL_CRITERIA_20260530.md",
    [string]$CadenceDoc = "docs/release/CERTIFICATION_EXPIRY_REVALIDATION_CADENCE_20260530.md",
    [string]$NamingDoc = "docs/release/EVIDENCE_ARTIFACT_NAMING_STANDARD_20260530.md",
    [string]$EvidenceIndex = "docs/release/EVIDENCE_PACKET_INDEX_ACTIVE_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requiredFiles = @($PassCriteria, $FailCriteria, $CadenceDoc, $NamingDoc, $EvidenceIndex)
$missing = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Output "POLICY_FILE_MISSING $_" }
    Write-Error "certification policy artifact check failed"
    exit 1
}

$indexText = Get-Content -Raw -Path $EvidenceIndex
$indexRows = ([regex]::Matches($indexText, "\|\s*EV-\d{3}\s*\|")).Count
if ($indexRows -lt 10) {
    Write-Error "active evidence packet index must contain at least 10 artifacts"
    exit 1
}

# Validate filename pattern for indexed artifacts.
$lineMatches = [regex]::Matches($indexText, "\|\s*EV-\d{3}\s*\|\s*([^|]+?)\s*\|")
$badNames = @()
foreach ($match in $lineMatches) {
    $pathValue = $match.Groups[1].Value.Trim()
    $fileName = [System.IO.Path]::GetFileName($pathValue)
    if ($fileName -notmatch '^[A-Za-z0-9_-]+\.(md|json|txt|csv|ps1)$') {
        $badNames += $fileName
    }
}

Write-Output "[certification-policy-artifacts] index_rows=$indexRows bad_names=$($badNames.Count)"
foreach ($name in $badNames) {
    Write-Output "BAD_ARTIFACT_NAME $name"
}

if ($badNames.Count -gt 0) {
    Write-Error "artifact naming policy check failed"
    exit 1
}

Write-Output "OK certification policy artifact check passed"
exit 0
