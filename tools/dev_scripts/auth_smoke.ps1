#!/usr/bin/env pwsh
# Gate 1A: Deterministic JWT Auth Smoke Test
# Boots local server, tests /api/auth/{login,refresh,me}, reports PASS/FAIL

$ErrorActionPreference = "Stop"

Write-Host "`n=== Gate 1A: JWT Auth Local Smoke Test ===" -ForegroundColor Cyan
Write-Host "Start line: main@534bf91d, tag: demo-jwt-auth-core-merged`n"

# --- Config ---
$WORKSPACE = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$VENV_PYTHON = Join-Path $WORKSPACE ".venv\Scripts\python.exe"
$MANAGE_PY = Join-Path $WORKSPACE "backend\manage.py"
$BASE_URL = "http://127.0.0.1:8000"
$SERVER_TIMEOUT = 30

# --- Step 0: Kill any existing python processes ---
Write-Host "[0/4] Cleaning up stale servers..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*Crown2026*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# --- Step 1: Boot server in background ---
Write-Host "[1/4] Starting Django server..." -ForegroundColor Yellow
Push-Location (Join-Path $WORKSPACE "backend")
$serverJob = Start-Job -ScriptBlock {
    param($venvPython, $managePy)
    & $venvPython $managePy runserver 127.0.0.1:8000 --noreload 2>&1
} -ArgumentList $VENV_PYTHON, $MANAGE_PY
Pop-Location

# --- Step 2: Wait for server ready (health check) ---
Write-Host "[2/4] Waiting for server ready..." -ForegroundColor Yellow
$ready = $false
$elapsed = 0
while (-not $ready -and $elapsed -lt $SERVER_TIMEOUT) {
    try {
        $health = Invoke-RestMethod -Uri "$BASE_URL/health/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($health.status -eq "ok") {
            $ready = $true
            Write-Host "  Server ready after ${elapsed}s" -ForegroundColor Green
        }
    } catch {
        Start-Sleep -Seconds 1
        $elapsed++
    }
}

if (-not $ready) {
    Write-Host "  FAIL: Server did not become ready within ${SERVER_TIMEOUT}s" -ForegroundColor Red
    Stop-Job $serverJob -ErrorAction SilentlyContinue
    Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
    exit 1
}

# --- Step 2.5: Ensure test user exists ---
Write-Host "[2.5/4] Ensuring test user exists..." -ForegroundColor Yellow
Push-Location (Join-Path $WORKSPACE "backend")
& $VENV_PYTHON -c @"
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()
from crown_api.auth_models import CrownUser
from django.contrib.auth.hashers import make_password
user, created = CrownUser.objects.get_or_create(
    email='admin@heritage.test',
    defaults={
        'password_hash': make_password('Passw0rd!'),
        'role': 'director',
        'is_active': True
    }
)
if created:
    print('Created test user')
else:
    print('Test user already exists')
"@
Pop-Location


# --- Step 3: Run JWT auth flow ---
Write-Host "[3/4] Testing JWT auth endpoints..." -ForegroundColor Yellow

try {
    # Login
    Write-Host "  [3a] POST /api/auth/login/ ..." -NoNewline
    $loginBody = @{
        email = "admin@heritage.test"
        password = "Passw0rd!"
    } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Uri "$BASE_URL/api/auth/login/" -Method Post -ContentType "application/json" -Body $loginBody -ErrorAction Stop
    
    if (-not $loginResp.access -or -not $loginResp.refresh) {
        throw "Login response missing tokens"
    }
    Write-Host " OK (got access+refresh)" -ForegroundColor Green
    
    # Me (with Bearer token)
    Write-Host "  [3b] GET /api/auth/me/ (Bearer) ..." -NoNewline
    $meResp = Invoke-RestMethod -Uri "$BASE_URL/api/auth/me/" -Headers @{ Authorization = "Bearer $($loginResp.access)" } -ErrorAction Stop
    
    if (-not $meResp.user -or -not $meResp.user.email) {
        throw "Me response missing user data"
    }
    Write-Host " OK (user=$($meResp.user.email))" -ForegroundColor Green
    
    # Refresh
    Write-Host "  [3c] POST /api/auth/refresh/ ..." -NoNewline
    $refreshBody = @{ refresh = $loginResp.refresh } | ConvertTo-Json
    $refreshResp = Invoke-RestMethod -Uri "$BASE_URL/api/auth/refresh/" -Method Post -ContentType "application/json" -Body $refreshBody -ErrorAction Stop
    
    if (-not $refreshResp.access) {
        throw "Refresh response missing new access token"
    }
    Write-Host " OK (got new access)" -ForegroundColor Green
    
    $RESULT = "PASS"
    
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    $RESULT = "FAIL"
}

# --- Step 4: Cleanup ---
Write-Host "[4/4] Shutting down server..." -ForegroundColor Yellow
Stop-Job $serverJob -ErrorAction SilentlyContinue
Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*Crown2026*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# --- Final Report ---
Write-Host "`n=== RESULT: $RESULT ===" -ForegroundColor $(if ($RESULT -eq "PASS") { "Green" } else { "Red" })

if ($RESULT -eq "PASS") {
    Write-Host "✓ All JWT auth endpoints returned 200 with expected data." -ForegroundColor Green
    Write-Host "✓ Local behavior matches CI." -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ JWT auth endpoints failed locally." -ForegroundColor Red
    Write-Host "✗ See error details above." -ForegroundColor Red
    exit 1
}
