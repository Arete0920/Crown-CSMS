param(
    [string]$Base = "origin/main",
    [string]$Head = "HEAD"
)

$ErrorActionPreference = "Stop"

$RepoRoot = git rev-parse --show-toplevel
Set-Location $RepoRoot

$ForbiddenClaims = @(
    "production ready", # forbidden claim
    "release ready", # forbidden claim
    "sandbox ready", # forbidden claim
    "dashboard live-data complete", # forbidden claim
    "wizard functional-flow complete", # forbidden claim
    "all wizards complete", # forbidden claim
    "all modules complete", # forbidden claim
    "independently approved", # forbidden claim
    "fully certified" # forbidden claim
)

$AllowedEvidenceMarkers = @(
    "INDEPENDENT_REVIEW_REQUIRED",
    "NOT_VERIFIED",
    "OUT_OF_SCOPE",
    "does not claim",
    "does not certify",
    "forbidden claim",
    "forbidden claims",
    "Scope Boundary",
    "Scope boundary"
)

$ChangedFiles = @(git diff --name-only "$Base...$Head" -- 2>$null)
if (-not $ChangedFiles -or $ChangedFiles.Count -eq 0) {
    Write-Host "CROWN forbidden-claims guard: no changed files."
    exit 0
}

$TextFiles = @()
foreach ($file in $ChangedFiles) {
    if (-not (Test-Path $file)) { continue }
    if ($file -match "\.(md|txt|csv|json|yml|yaml|py|ps1|ts|tsx|js|jsx)$") {
        $TextFiles += $file
    }
}

$Findings = @()
foreach ($file in $TextFiles) {
    $lines = Get-Content -LiteralPath $file -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = [string]$lines[$i]
        $lower = $line.ToLowerInvariant()
        foreach ($claim in $ForbiddenClaims) {
            if ($lower.Contains($claim.ToLowerInvariant())) {
                $hasMarker = $false
                foreach ($marker in $AllowedEvidenceMarkers) {
                    if ($line.Contains($marker)) { $hasMarker = $true }
                }
                if (-not $hasMarker) {
                    $Findings += [pscustomobject]@{
                        File = $file
                        Line = $i + 1
                        Claim = $claim
                        Text = $line.Trim()
                    }
                }
            }
        }
    }
}

if ($Findings.Count -gt 0) {
    Write-Host "CROWN forbidden-claims guard: FAIL"
    $Findings | Format-Table -AutoSize | Out-String | Write-Host
    Write-Host "Use bounded language or add an explicit boundary marker such as NOT_VERIFIED or INDEPENDENT_REVIEW_REQUIRED."
    exit 1
}

Write-Host "CROWN forbidden-claims guard: PASS"
exit 0
