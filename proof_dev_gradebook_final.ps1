#!/usr/bin/env pwsh
<#
.SYNOPSIS
    DEV environment proof: verify gradebook data after ops reset.
.DESCRIPTION
    Pulls CROWN_DEMO_PASSWORD from Azure, authenticates, and verifies:
    - Health endpoint responds
    - Sections exist
    - Gradebook assignments populated
    Zero secrets printed. Exit 0 on success, non-zero on failure.
#>

$ErrorActionPreference = "Stop"

# Configuration
$base = "https://crown-api-dev.azurewebsites.net"
$schoolId = "a5351136-98fe-4d48-add0-fa8f62d9ceff"
$resourceGroup = "crown-rg"
$appName = "crown-api-dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DEV Gradebook Proof" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Metrics collection
$metrics = @{
    health_ok = $false
    auth_ok = $false
    sections_count = 0
    assignment_count = 0
    student_count = 0
    build_sha = ""
}

# Step 1: Health Check
Write-Host "[1/4] Health..." -NoNewline
try {
    $health = Invoke-RestMethod -Uri "$base/health/" -Method GET -ErrorAction Stop
    if ($health.ok -eq $true) {
        $metrics.health_ok = $true
        $metrics.build_sha = $health.build_sha.Substring(0,8)
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAIL" -ForegroundColor Red
        throw "Health endpoint returned ok=$($health.ok)"
    }
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Get Password from Azure (no echo)
Write-Host "[2/4] Azure config..." -NoNewline
try {
    $demoPw = az webapp config appsettings list `
      --resource-group $resourceGroup `
      --name $appName `
      --query "[?name=='CROWN_DEMO_PASSWORD'].value | [0]" `
      -o tsv 2>$null
    
    if (-not $demoPw) {
        Write-Host " FAIL" -ForegroundColor Red
        Write-Host "  CROWN_DEMO_PASSWORD not found in Azure App Settings" -ForegroundColor Red
        exit 1
    }
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error reading Azure config: $_" -ForegroundColor Red
    Write-Host "  Ensure Azure CLI is authenticated (az login)" -ForegroundColor Yellow
    exit 1
}

# Step 3: Authentication (no token output)
Write-Host "[3/4] Auth..." -NoNewline
try {
    $loginBody = @{ 
        username = "admin"
        password = $demoPw
    } | ConvertTo-Json
    
    $loginResp = Invoke-RestMethod -Method POST `
      -Uri "$base/api/v1/auth/token/" `
      -ContentType "application/json" `
      -Body $loginBody `
      -ErrorAction Stop
    
    $token = $loginResp.access
    
    if (-not $token) {
        Write-Host " FAIL" -ForegroundColor Red
        throw "No token returned"
    }
    
    $metrics.auth_ok = $true
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  Detail: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

# Step 4: Gradebook Data
Write-Host "[4/4] Gradebook..." -NoNewline
try {
    $headers = @{
        Authorization = "Bearer $token"
        "Content-Type" = "application/json"
        "X-School-Id" = $schoolId
    }
    
    # 4a) Sections list
    $sectionsResp = Invoke-RestMethod -Method GET `
      -Uri "$base/api/v1/gradebook/sections/" `
      -Headers $headers `
      -ErrorAction Stop
    
    $sectionsCount = if ($sectionsResp -is [System.Array]) {
        $sectionsResp.Count
    } elseif ($sectionsResp.results) {
        $sectionsResp.results.Count
    } else {
        0
    }
    
    $metrics.sections_count = $sectionsCount
    
    if ($sectionsCount -lt 1) {
        Write-Host " FAIL" -ForegroundColor Red
        Write-Host "  No sections found" -ForegroundColor Red
        exit 1
    }
    
    # 4b) Section summary (verify assignments)
    $sectionId = if ($sectionsResp -is [System.Array]) {
        $sectionsResp[0].section_id
    } else {
        $sectionsResp.results[0].section_id
    }
    
    $summaryResp = Invoke-RestMethod -Method GET `
      -Uri "$base/api/v1/gradebook/sections/$sectionId/summary/" `
      -Headers $headers `
      -ErrorAction Stop
    
    # Extract assignment count (handle different response shapes)
    $assignmentCount = 0
    if ($summaryResp.assignment_count -ne $null) {
        $assignmentCount = [int]$summaryResp.assignment_count
    } elseif ($summaryResp.totals -and $summaryResp.totals.assignment_count -ne $null) {
        $assignmentCount = [int]$summaryResp.totals.assignment_count
    } elseif ($summaryResp.assignments -ne $null) {
        if ($summaryResp.assignments -is [System.Array]) {
            $assignmentCount = $summaryResp.assignments.Count
        } else {
            $assignmentCount = [int]$summaryResp.assignments
        }
    }
    
    $metrics.assignment_count = $assignmentCount
    $metrics.student_count = if ($summaryResp.student_count) { [int]$summaryResp.student_count } else { 0 }
    
    if ($assignmentCount -lt 1) {
        Write-Host " FAIL" -ForegroundColor Red
        Write-Host "  Zero assignments in summary" -ForegroundColor Red
        exit 1
    }
    
    Write-Host " OK" -ForegroundColor Green
    
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Final Report
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PASS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor White
Write-Host "  Health:      OK (build $($metrics.build_sha))" -ForegroundColor Gray
Write-Host "  Auth:        OK" -ForegroundColor Gray
Write-Host "  Sections:    $($metrics.sections_count)" -ForegroundColor Gray
Write-Host "  Assignments: $($metrics.assignment_count)" -ForegroundColor Gray
Write-Host "  Students:    $($metrics.student_count)" -ForegroundColor Gray
Write-Host ""

exit 0
