#!/usr/bin/env powershell

param(
    [switch]$SkipChecks,
    [int]$BackendWait = 3,
    [int]$FrontendWait = 4,
    [int]$APITimeout = 10
)

$ErrorActionPreference = 'Stop'
$WarningPreference = 'SilentlyContinue'

function Resolve-NpmCmd {
    [CmdletBinding()]
    param()

    $candidates = @("npm.cmd", "npm")
    foreach ($name in $candidates) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Path -and (Test-Path $cmd.Path)) {
            return $cmd.Path
        }
    }
    throw "npm not found. Install Node.js LTS and ensure npm is on PATH."
}

$script:NPM_CMD = Resolve-NpmCmd

$TAG = "demo-feb16-gradebook-edit-pp-001"
$USERNAME = "head@crown-demo.local"
$PASSWORD = "demo1234"
$SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962"
$BACKEND_URL = "http://127.0.0.1:8000"
$FRONTEND_URL = "http://127.0.0.1:3000"

$SCRIPT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Write-Host "Demo Boot Script Started" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor DarkGray

Write-Host ""
Write-Host "Step 1: Checking out tag..." -ForegroundColor Yellow
try {
    Push-Location $SCRIPT_ROOT -ErrorAction Ignore
    & git fetch origin --tags | Out-Null 2>&1
    & git checkout $TAG -f | Out-Null 2>&1
    Write-Host "  [OK] Tag checked out" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Git checkout failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Step 2: Starting Django backend..." -ForegroundColor Yellow
$backendProc = $null
try {
    Push-Location "$SCRIPT_ROOT\backend"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    $env:PYTHONUNBUFFERED = "1"
    
    $backendProc = Start-Process -NoNewWindow `
        -FilePath "$SCRIPT_ROOT\.venv\Scripts\python.exe" `
        -ArgumentList @("manage.py", "runserver", "127.0.0.1:8000", "--noreload") `
        -PassThru
    
    Write-Host "  (PID: $($backendProc.Id)) Waiting ${BackendWait}s..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $BackendWait
} catch {
    Write-Host "  [FAIL] Backend startup failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Step 3: Starting React frontend..." -ForegroundColor Yellow
$frontendProc = $null
try {
    # Enable demo mode to hide dev panels
    $env:VITE_DEMO_MODE = "1"
    
    $frontendProc = Start-Process -FilePath $script:NPM_CMD `
        -ArgumentList @("--prefix", "$SCRIPT_ROOT\frontend\dashboards", "run", "dev", "--", "--port", "3000") `
        -WindowStyle Minimized `
        -PassThru
    
    Write-Host "  (PID: $($frontendProc.Id)) Waiting ${FrontendWait}s..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $FrontendWait
} catch {
    Write-Host "  [FAIL] Frontend startup failed: $_" -ForegroundColor Red
    if ($backendProc) { Stop-Process -InputObject $backendProc -ErrorAction Ignore }
    exit 1
}

Write-Host ""
Write-Host "Step 4: Running API sanity checks..." -ForegroundColor Yellow

if ($SkipChecks) {
    Write-Host "  [SKIP] Skipping API checks" -ForegroundColor DarkGray
} else {
    $checksPass = $true
    $token = $null
    $sectionId = $null
    
    Write-Host "  -> Authentication..." -ForegroundColor DarkGray
    try {
        $response = Invoke-RestMethod `
            -Uri "$BACKEND_URL/api/v1/auth/token/" `
            -Method Post `
            -ContentType "application/json" `
            -Body (@{ username = $USERNAME; password = $PASSWORD } | ConvertTo-Json) `
            -TimeoutSec $APITimeout `
            -ErrorAction Stop
        
        if ($response.access) {
            $token = $response.access
            Write-Host "    [OK] Token acquired" -ForegroundColor Green
        } else {
            Write-Host "    [FAIL] No token in response" -ForegroundColor Red
            $checksPass = $false
        }
    } catch {
        Write-Host "    [FAIL] Auth failed: $_" -ForegroundColor Red
        $checksPass = $false
    }
    
    if ($checksPass) {
        Write-Host "  -> Sections..." -ForegroundColor DarkGray
        try {
            $headers = @{ Authorization = "Bearer $token"; "X-School-Id" = $SCHOOL_ID }
            $sectionsResponse = Invoke-RestMethod `
                -Uri "$BACKEND_URL/api/v1/academics/sections/" `
                -Headers $headers `
                -TimeoutSec $APITimeout `
                -ErrorAction Stop
            
            $sectionCount = $sectionsResponse.results.Count
            if ($sectionCount -gt 0) {
                $sectionId = $sectionsResponse.results[0].section_id
                Write-Host "    [OK] $sectionCount sections loaded" -ForegroundColor Green
            } else {
                Write-Host "    [FAIL] No sections returned" -ForegroundColor Red
                $checksPass = $false
            }
        } catch {
            Write-Host "    [FAIL] Sections failed: $_" -ForegroundColor Red
            $checksPass = $false
        }
    }
    
    if ($checksPass -and $sectionId) {
        Write-Host "  -> Gradebook..." -ForegroundColor DarkGray
        try {
            $gradesResponse = Invoke-RestMethod `
                -Uri "$BACKEND_URL/api/v1/gradebook/sections/$sectionId/grades/" `
                -Headers $headers `
                -TimeoutSec $APITimeout `
                -ErrorAction Stop
            
            $assignmentCount = $gradesResponse.assignments.Count
            $rowCount = $gradesResponse.rows.Count
            
            $fkSample = $gradesResponse.assignments[0]
            if ($fkSample.assignment_name -and $fkSample.points_possible) {
                Write-Host "    [OK] $assignmentCount assignments, $rowCount rows (FK-backed)" -ForegroundColor Green
            } else {
                Write-Host "    [WARN] Data present but FK-backed fields missing" -ForegroundColor Yellow
                $checksPass = $false
            }
        } catch {
            Write-Host "    [FAIL] Gradebook failed: $_" -ForegroundColor Red
            $checksPass = $false
        }
    }
    
    if (-not $checksPass) {
        Write-Host ""
        Write-Host "  [WARN] Some checks failed. Verify manually." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host "[OK] Demo Boot Complete" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Open browser: $FRONTEND_URL" -ForegroundColor White
Write-Host "2. Login (developer modal or standard login):" -ForegroundColor White
Write-Host "   Username: $USERNAME" -ForegroundColor DarkYellow
Write-Host "   Password: $PASSWORD" -ForegroundColor DarkYellow
Write-Host "3. Navigate to section, open Gradebook, edit points_possible" -ForegroundColor White
Write-Host ""
Write-Host "Servers Running:" -ForegroundColor Cyan
Write-Host "  Backend:  $BACKEND_URL  (PID: $($backendProc.Id))" -ForegroundColor DarkGray
Write-Host "  Frontend: $FRONTEND_URL (PID: $($frontendProc.Id))" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press Ctrl+C to stop servers" -ForegroundColor DarkGray
Write-Host "================================================================" -ForegroundColor DarkGray

try {
    while ($true) {
        if ($backendProc.HasExited -or $frontendProc.HasExited) {
            Write-Host ""
            Write-Host "[WARN] A process exited. Cleaning up..." -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "Monitoring error: $_" -ForegroundColor Yellow
} finally {
    if ($backendProc -and -not $backendProc.HasExited) { Stop-Process -InputObject $backendProc -ErrorAction Ignore }
    if ($frontendProc -and -not $frontendProc.HasExited) { Stop-Process -InputObject $frontendProc -ErrorAction Ignore }
    Write-Host "Shutdown complete." -ForegroundColor Green
}
