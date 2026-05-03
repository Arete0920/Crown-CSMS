$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = "audit-artifacts\post-azure-live-proof\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

$BackendBaseUrl = "https://crown-api-prod.azurewebsites.net"
$FrontendBaseUrl = "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net"
$ApprovedSha = "b9dad81"

function Get-Status {
    param([string]$Url)

    try {
        return (curl.exe -s -o NUL -w "%{http_code}" -L -m 20 $Url)
    }
    catch {
        return "ERROR"
    }
}

function Get-Body {
    param([string]$Url)

    try {
        return (curl.exe -s -L -m 20 $Url)
    }
    catch {
        return ""
    }
}

$BackendHealthUrl = "$BackendBaseUrl/api/health/"
$FrontendRootUrl = "$FrontendBaseUrl/"
$BuildJsonUrl = "$FrontendBaseUrl/build.json"

$BackendStatus = Get-Status $BackendHealthUrl
$FrontendStatus = Get-Status $FrontendRootUrl
$BuildJsonStatus = Get-Status $BuildJsonUrl
$BackendBody = Get-Body $BackendHealthUrl
$BuildJsonBody = Get-Body $BuildJsonUrl

$BackendBody | Set-Content (Join-Path $Out "backend_health_body.txt") -Encoding UTF8
$BuildJsonBody | Set-Content (Join-Path $Out "frontend_build_json_body.txt") -Encoding UTF8

$BackendShaMatch = $BackendBody -match [regex]::Escape($ApprovedSha)
$FrontendShaMatch = $BuildJsonBody -match [regex]::Escape($ApprovedSha)

$Rows = @(
    [pscustomobject]@{ Gate = "Backend health HTTP 200"; Status = $(if ($BackendStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $BackendStatus; Required = "200"; Evidence = "backend_health_body.txt" },
    [pscustomobject]@{ Gate = "Backend approved SHA"; Status = $(if ($BackendShaMatch) { "PASS" } else { "FAIL" }); Actual = $BackendShaMatch; Required = $ApprovedSha; Evidence = "backend_health_body.txt" },
    [pscustomobject]@{ Gate = "Frontend root HTTP 200"; Status = $(if ($FrontendStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $FrontendStatus; Required = "200"; Evidence = "" },
    [pscustomobject]@{ Gate = "Frontend build.json HTTP 200"; Status = $(if ($BuildJsonStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $BuildJsonStatus; Required = "200"; Evidence = "frontend_build_json_body.txt" },
    [pscustomobject]@{ Gate = "Frontend approved SHA"; Status = $(if ($FrontendShaMatch) { "PASS" } else { "FAIL" }); Actual = $FrontendShaMatch; Required = $ApprovedSha; Evidence = "frontend_build_json_body.txt" }
)

$Rows | Export-Csv (Join-Path $Out "POST_AZURE_LIVE_PROOF.csv") -NoTypeInformation -Encoding UTF8

$FailCount = @($Rows | Where-Object { $_.Status -eq "FAIL" }).Count
if ($FailCount -eq 0) {
    $Decision = "AZURE_LIVE_PROOF_PASS"
}
else {
    $Decision = "AZURE_LIVE_PROOF_FAIL"
}

@"
# CROWN Post-Azure Live Proof

Generated: $(Get-Date -Format s)

- Decision: $Decision
- BackendStatus: $BackendStatus
- BackendShaMatch: $BackendShaMatch
- FrontendStatus: $FrontendStatus
- BuildJsonStatus: $BuildJsonStatus
- FrontendShaMatch: $FrontendShaMatch
- Output: $Out

## Rows

$($Rows | Format-Table -AutoSize | Out-String)
"@ | Set-Content (Join-Path $Out "POST_AZURE_SUMMARY.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window (Join-Path $Out "POST_AZURE_SUMMARY.md") | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $Out "POST_AZURE_LIVE_PROOF.csv") | Out-Null
}

Write-Host ""
Write-Host "Post-Azure proof decision: $Decision"
Write-Host "Output: $Out"
Write-Host ""
