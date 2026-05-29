param(
    [string]$HealthUrl = "",
    [string]$IntegrityUrl = "",
    [string]$HealthJsonPath = "",
    [string]$IntegrityJsonPath = "",
    [string]$DeployTargetSha = "",
    [string]$ApprovedReleaseSha = "",
    [string]$OutputDir = "docs/release/live-audit/deploy-sha-parity",
    [switch]$FailOnOpen
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)
    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Try-GetBuildSha {
    param([string]$Url)
    if ([string]::IsNullOrWhiteSpace($Url)) {
        return $null
    }

    try {
        $resp = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30
        return Extract-BuildShaFromPayload -Payload $resp
    }
    catch {
        return $null
    }
}

function Extract-BuildShaFromPayload {
    param($Payload)

    if ($null -eq $Payload) {
        return $null
    }

    $obj = $Payload
    if ($obj -is [string]) {
        try {
            $obj = $obj | ConvertFrom-Json
        }
        catch {
            return $null
        }
    }

    if ($null -eq $obj) {
        return $null
    }

    if ($obj.PSObject.Properties.Name -contains "build_sha") {
        $direct = [string]$obj.build_sha
        if (-not [string]::IsNullOrWhiteSpace($direct)) {
            return $direct
        }
    }

    if ($obj.PSObject.Properties.Name -contains "body") {
        $body = $obj.body
        $bodyObj = $body

        if ($body -is [string]) {
            try {
                $bodyObj = $body | ConvertFrom-Json
            }
            catch {
                $bodyObj = $null
            }
        }

        if ($null -ne $bodyObj -and $bodyObj.PSObject.Properties.Name -contains "build_sha") {
            $nested = [string]$bodyObj.build_sha
            if (-not [string]::IsNullOrWhiteSpace($nested)) {
                return $nested
            }
        }
    }

    return $null
}

function Try-GetBuildShaFromJsonFile {
    param([string]$JsonPath)

    if ([string]::IsNullOrWhiteSpace($JsonPath)) {
        return $null
    }

    try {
        $resolved = Resolve-Path -Path $JsonPath -ErrorAction Stop
        $raw = Get-Content -Path $resolved -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json
        return Extract-BuildShaFromPayload -Payload $obj
    }
    catch {
        return $null
    }
}

function Normalize-Sha {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }
    return $Value.Trim().ToLowerInvariant()
}

$repoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $repoRoot

$headSha = Normalize-Sha (Invoke-Git -Args @("rev-parse", "HEAD"))
$originMainSha = Normalize-Sha (Invoke-Git -Args @("rev-parse", "--verify", "origin/main"))
$aheadBehind = Invoke-Git -Args @("rev-list", "--left-right", "--count", "origin/main...HEAD")

$approvedSha = Normalize-Sha $ApprovedReleaseSha
if ([string]::IsNullOrWhiteSpace($approvedSha)) {
    $approvedSha = $originMainSha
}

$healthBuildSha = Normalize-Sha (Try-GetBuildSha -Url $HealthUrl)
if ([string]::IsNullOrWhiteSpace($healthBuildSha)) {
    $healthBuildSha = Normalize-Sha (Try-GetBuildShaFromJsonFile -JsonPath $HealthJsonPath)
}

$integrityBuildSha = Normalize-Sha (Try-GetBuildSha -Url $IntegrityUrl)
if ([string]::IsNullOrWhiteSpace($integrityBuildSha)) {
    $integrityBuildSha = Normalize-Sha (Try-GetBuildShaFromJsonFile -JsonPath $IntegrityJsonPath)
}

$deployTargetShaNorm = Normalize-Sha $DeployTargetSha

$evidenceShas = @()
if (-not [string]::IsNullOrWhiteSpace($deployTargetShaNorm)) { $evidenceShas += $deployTargetShaNorm }
if (-not [string]::IsNullOrWhiteSpace($healthBuildSha)) { $evidenceShas += $healthBuildSha }
if (-not [string]::IsNullOrWhiteSpace($integrityBuildSha)) { $evidenceShas += $integrityBuildSha }

$allEvidenceMatchesApproved = $true
$allEvidenceMatchesHead = $true

if ($evidenceShas.Count -eq 0) {
    $allEvidenceMatchesApproved = $false
    $allEvidenceMatchesHead = $false
}
else {
    foreach ($sha in $evidenceShas) {
        if ($sha -ne $approvedSha) {
            $allEvidenceMatchesApproved = $false
        }
        if ($sha -ne $headSha) {
            $allEvidenceMatchesHead = $false
        }
    }
}

$parityClosed = $allEvidenceMatchesApproved -or $allEvidenceMatchesHead
$parityStatus = if ($parityClosed) { "CLOSED" } else { "OPEN" }

$timestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$outDirAbs = Join-Path $repoRoot ($OutputDir -replace '/', '\\')
New-Item -ItemType Directory -Force -Path $outDirAbs | Out-Null

$jsonOut = Join-Path $outDirAbs "deploy_sha_parity_$timestampUtc.json"
$mdOut = Join-Path $outDirAbs "deploy_sha_parity_$timestampUtc.md"

$result = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $repoRoot
    git = [ordered]@{
        head_sha = $headSha
        origin_main_sha = $originMainSha
        ahead_behind_origin_main = $aheadBehind
        approved_release_sha = $approvedSha
    }
    runtime_evidence = [ordered]@{
        health_url = $HealthUrl
        integrity_url = $IntegrityUrl
        health_json_path = $HealthJsonPath
        integrity_json_path = $IntegrityJsonPath
        deploy_target_sha = $deployTargetShaNorm
        health_build_sha = $healthBuildSha
        integrity_build_sha = $integrityBuildSha
    }
    evaluation = [ordered]@{
        parity_status = $parityStatus
        parity_closed = $parityClosed
        evidence_count = $evidenceShas.Count
        matches_approved_release_sha = $allEvidenceMatchesApproved
        matches_local_head_sha = $allEvidenceMatchesHead
    }
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonOut -Encoding UTF8

$md = @"
# Deploy SHA Parity Capture

Generated UTC: $($result.generated_at_utc)

## Git Snapshot
- head_sha: $headSha
- origin_main_sha: $originMainSha
- ahead_behind_origin_main: $aheadBehind
- approved_release_sha: $approvedSha

## Runtime Evidence
- health_url: $HealthUrl
- integrity_url: $IntegrityUrl
- health_json_path: $HealthJsonPath
- integrity_json_path: $IntegrityJsonPath
- deploy_target_sha: $deployTargetShaNorm
- health_build_sha: $healthBuildSha
- integrity_build_sha: $integrityBuildSha

## Evaluation
- parity_status: $parityStatus
- parity_closed: $parityClosed
- evidence_count: $($evidenceShas.Count)
- matches_approved_release_sha: $allEvidenceMatchesApproved
- matches_local_head_sha: $allEvidenceMatchesHead
"@

Set-Content -Path $mdOut -Value $md -Encoding UTF8

Write-Host "Deploy SHA parity capture written:" -ForegroundColor Cyan
Write-Host "  $jsonOut"
Write-Host "  $mdOut"
Write-Host "Parity status: $parityStatus" -ForegroundColor $(if ($parityClosed) { "Green" } else { "Yellow" })

if ($FailOnOpen -and -not $parityClosed) {
    exit 2
}

exit 0
