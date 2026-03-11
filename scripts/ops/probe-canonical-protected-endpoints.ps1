param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$Token,

    [Parameter(Mandatory = $true)]
    [string]$SchoolId,

    [Parameter(Mandatory = $true)]
    [string]$WrongSchoolId
)

$ErrorActionPreference = "Stop"

$Endpoints = @(
    "/api/v1/admissions/summary/",
    "/api/v1/finance/metrics/",
    "/api/v1/board/dashboard/"
)

$OutputDir = "_warroom"
$OutputFile = Join-Path $OutputDir "protected_endpoint_proof.txt"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Invoke-Probe {
    param(
        [string]$Url,
        [hashtable]$Headers
    )

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    try {
        $response = Invoke-WebRequest -Uri $Url -Headers $Headers -Method GET -SkipHttpErrorCheck
        return [PSCustomObject]@{
            Timestamp  = $ts
            StatusCode = [int]$response.StatusCode
            Body       = $response.Content
        }
    }
    catch {
        return [PSCustomObject]@{
            Timestamp  = $ts
            StatusCode = -1
            Body       = $_.Exception.Message
        }
    }
}

$lines = @()
$lines += "CROWN2026 CANONICAL PROTECTED ENDPOINT PROOF"
$lines += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += ""

foreach ($endpoint in $Endpoints) {
    $url = "$BaseUrl$endpoint"

    $headersNoTenant = @{
        Authorization = "Bearer $Token"
    }

    $headersWrongTenant = @{
        Authorization = "Bearer $Token"
        "X-School-Id" = $WrongSchoolId
    }

    $headersCorrectTenant = @{
        Authorization = "Bearer $Token"
        "X-School-Id" = $SchoolId
    }

    $resultNoAuth = Invoke-Probe -Url $url -Headers @{}
    $resultAuthNoTenant = Invoke-Probe -Url $url -Headers $headersNoTenant
    $resultWrongTenant = Invoke-Probe -Url $url -Headers $headersWrongTenant
    $resultCorrectTenant = Invoke-Probe -Url $url -Headers $headersCorrectTenant

    $lines += "ENDPOINT: $endpoint"
    $lines += "URL: $url"
    $lines += ""
    $lines += "case: no auth"
    $lines += "timestamp: $($resultNoAuth.Timestamp)"
    $lines += "status: $($resultNoAuth.StatusCode)"
    $lines += "body: $($resultNoAuth.Body)"
    $lines += ""
    $lines += "case: valid auth, no tenant"
    $lines += "timestamp: $($resultAuthNoTenant.Timestamp)"
    $lines += "status: $($resultAuthNoTenant.StatusCode)"
    $lines += "body: $($resultAuthNoTenant.Body)"
    $lines += ""
    $lines += "case: valid auth, wrong tenant"
    $lines += "timestamp: $($resultWrongTenant.Timestamp)"
    $lines += "status: $($resultWrongTenant.StatusCode)"
    $lines += "body: $($resultWrongTenant.Body)"
    $lines += ""
    $lines += "case: valid auth, correct tenant"
    $lines += "timestamp: $($resultCorrectTenant.Timestamp)"
    $lines += "status: $($resultCorrectTenant.StatusCode)"
    $lines += "body: $($resultCorrectTenant.Body)"
    $lines += ""
    $lines += ("-" * 80)
    $lines += ""
}

$lines | Set-Content -Path $OutputFile -Encoding UTF8

Write-Host "Proof written to $OutputFile"
