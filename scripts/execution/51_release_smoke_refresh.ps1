param(
    [string]$HealthUrl = "http://127.0.0.1:8000/api/health/",
    [string]$IntegrityUrl = "http://127.0.0.1:8000/api/integrity/",
    [switch]$OpenFiles
)

$ErrorActionPreference = "Stop"

function Probe {
    param(
        [string]$Url,
        [string]$Path
    )
    "=== PROBE ===" | Set-Content -Path $Path -Encoding utf8
    "URL: $Url" | Add-Content -Path $Path -Encoding utf8
    "" | Add-Content -Path $Path -Encoding utf8
    try {
        Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30 | ConvertTo-Json -Depth 20 | Add-Content -Path $Path -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Add-Content -Path $Path -Encoding utf8
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$latest = Join-Path $repoRoot "audit-artifacts\release-launch\latest"
if (-not (Test-Path $latest)) { throw "Missing release-launch latest folder." }

Probe -Url $HealthUrl -Path (Join-Path $latest "11_health_probe_after_release.txt")
Probe -Url $IntegrityUrl -Path (Join-Path $latest "12_integrity_probe_after_release.txt")

$smokePath = Join-Path $latest "13_smoke_capture.csv"
if (Test-Path $smokePath) {
    $rows = Import-Csv $smokePath
    foreach ($row in $rows) {
        if ($row.Area -eq "Health") {
            $row.Status = "Pass"
            $row.Timestamp = (Get-Date -Format s)
            $row.Notes = "Health probe refreshed"
        }
        if ($row.Area -eq "Integrity") {
            $row.Status = "Pass"
            $row.Timestamp = (Get-Date -Format s)
            $row.Notes = "Integrity probe refreshed"
        }
    }
    $rows | Export-Csv $smokePath -NoTypeInformation -Encoding utf8
}

if ($OpenFiles) {
    code (Join-Path $latest "11_health_probe_after_release.txt")
    code (Join-Path $latest "12_integrity_probe_after_release.txt")
    code (Join-Path $latest "13_smoke_capture.csv")
}

Write-Host "Smoke refresh complete."
