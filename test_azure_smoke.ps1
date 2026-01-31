#!/usr/bin/env pwsh
<#
.SYNOPSIS
Smoke test for Azure DEV Financial Aid API endpoints.
Verifies auth, routing, and contract compliance after deployment.

.DESCRIPTION
Reads credentials from environment variables or prompts securely.
Never passes credentials on command line.

.EXAMPLE
# Set in PowerShell or .env.local:
$env:CROWN_USERNAME = "head@crown-demo.local"
$env:CROWN_PASSWORD = "your-secure-password"
.\test_azure_smoke.ps1
#>

param(
    [string]$ApiUrl = "https://crown-api-dev.azurewebsites.net",
    [string]$SchoolId = "a5351136-98fe-4d48-add0-fa8f62d9ceff"
)

# Load .env.local if present (never committed)
if (Test-Path ".env.local") {
    Get-Content ".env.local" | ForEach-Object {
        if ($_ -match "^\s*([A-Z_]+)\s*=\s*(.+)\s*$") {
            $key = $matches[1]
            $value = $matches[2] -replace '["'\'']', ''
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Get credentials from env or prompt securely
$username = $env:CROWN_USERNAME
$password = $env:CROWN_PASSWORD

if (-not $username) {
    $username = Read-Host "Username"
}

if (-not $password) {
    $secureStr = Read-Host "Password" -AsSecureString
    $password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureStr)
    )
}

function Test-JsonKeys {
    param($obj, [string[]]$keys, [string]$testName)
    $missing = $keys | Where-Object { $_ -notin $obj.PSObject.Properties.Name }
    if ($missing) {
        Write-Error "[FAIL] $testName - Missing keys: $($missing -join ', ')"
        return $false
    }
    Write-Host "[PASS] $testName - All required keys present" -ForegroundColor Green
    return $true
}

Write-Host "`n=== Financial Aid Smoke Test ===" -ForegroundColor Cyan
Write-Host "API: $ApiUrl`n"

# 1. Get token
Write-Host "[1] Requesting auth token..." -ForegroundColor Yellow
try {
    $body = @{ username=$Username; password=$Password } | ConvertTo-Json -Compress
    $tokenResp = Invoke-RestMethod -Uri "$ApiUrl/api/v1/auth/token/" `
        -Method Post -ContentType "application/json" -Body $body -ErrorAction Stop
    $token = $tokenResp.access
    Write-Host "[PASS] Token obtained (length: $($token.Length))" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Auth failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Test summary endpoint
Write-Host "`n[2] Testing /api/v1/financial-aid/summary/..." -ForegroundColor Yellow
try {
    $summaryResp = Invoke-RestMethod -Uri "$ApiUrl/api/v1/financial-aid/summary/" `
        -Method Get `
        -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$SchoolId} `
        -ErrorAction Stop
    
    Write-Host "[PASS] Summary endpoint returned 200" -ForegroundColor Green
    
    # Validate contract
    $summaryKeys = @("academic_year", "totals", "awards_by_bucket")
    $totalsKeys = @("applications_total", "applications_by_status", "awards_total_count", "awards_total_amount", "avg_award_amount")
    $bucketKeys = @("need", "mission", "marketing", "merit", "hardship")
    
    Test-JsonKeys $summaryResp $summaryKeys "Summary root keys" | Out-Null
    Test-JsonKeys $summaryResp.totals $totalsKeys "Totals keys" | Out-Null
    Test-JsonKeys $summaryResp.awards_by_bucket $bucketKeys "Bucket keys" | Out-Null
    
    Write-Host "   Academic Year: $($summaryResp.academic_year)"
    Write-Host "   Total Applications: $($summaryResp.totals.applications_total)"
    Write-Host "   Total Awards: $($summaryResp.totals.awards_total_count)"
} catch {
    Write-Host "[FAIL] Summary endpoint failed: $_" -ForegroundColor Red
    exit 1
}

# 3. Test drilldown endpoint
Write-Host "`n[3] Testing /api/v1/financial-aid/drilldown/?bucket=need..." -ForegroundColor Yellow
try {
    $drilldownResp = Invoke-RestMethod -Uri "$ApiUrl/api/v1/financial-aid/drilldown/?bucket=need&limit=5&offset=0" `
        -Method Get `
        -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$SchoolId} `
        -ErrorAction Stop
    
    Write-Host "[PASS] Drilldown endpoint returned 200" -ForegroundColor Green
    
    # Validate contract
    $drilldownKeys = @("academic_year", "bucket", "count", "limit", "offset", "rows")
    Test-JsonKeys $drilldownResp $drilldownKeys "Drilldown keys" | Out-Null
    
    Write-Host "   Bucket: $($drilldownResp.bucket)"
    Write-Host "   Total Count: $($drilldownResp.count)"
    Write-Host "   Returned Rows: $($drilldownResp.rows.Count)"
    Write-Host "   Limit: $($drilldownResp.limit)"
    Write-Host "   Offset: $($drilldownResp.offset)"
} catch {
    Write-Host "[FAIL] Drilldown endpoint failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Test invalid bucket rejection
Write-Host "`n[4] Testing invalid bucket rejection..." -ForegroundColor Yellow
try {
    $invalidResp = Invoke-RestMethod -Uri "$ApiUrl/api/v1/financial-aid/drilldown/?bucket=invalid" `
        -Method Get `
        -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$SchoolId} `
        -ErrorAction Stop
    Write-Host "[FAIL] Expected 400 for invalid bucket, but got success" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "[PASS] Invalid bucket correctly rejected with 400" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Expected 400 but got: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        exit 1
    }
}

# 5. Test unauthenticated rejection
Write-Host "`n[5] Testing unauthenticated rejection..." -ForegroundColor Yellow
try {
    $unauthResp = Invoke-RestMethod -Uri "$ApiUrl/api/v1/financial-aid/summary/" `
        -Method Get `
        -Headers @{"X-School-Id"=$SchoolId} `
        -ErrorAction Stop
    Write-Host "[FAIL] Expected 403 for missing auth, but got success" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "[PASS] Unauthenticated request correctly rejected with 403" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Expected 403 but got: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n[SUCCESS] ALL SMOKE TESTS PASSED" -ForegroundColor Green
Write-Host "=============================`n"
exit 0
