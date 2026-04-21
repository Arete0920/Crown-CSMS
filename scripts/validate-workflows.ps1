# Validate workflow files before commit
# Run this before pushing any .github/workflows changes

$ErrorActionPreference = "Stop"

Write-Host "Validating workflow files..." -ForegroundColor Cyan

$workflowDir = ".github\workflows"
$files = Get-ChildItem $workflowDir -Filter *.yml

$errors = 0
$infos = 0

foreach ($file in $files) {
    Write-Host "`nChecking $($file.Name)..." -ForegroundColor Yellow
    
    # 1. Check encoding (should be UTF8 without BOM)
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Write-Host "  FAIL: UTF8-BOM detected (should be UTF8 no-BOM)" -ForegroundColor Red
        $errors++
    } else {
        Write-Host "  OK: Encoding OK (UTF8 no-BOM)" -ForegroundColor Green
    }
    
    # 2. Check for CRLF (should be LF only for GitHub Actions)
    $content = Get-Content $file.FullName -Raw
    if ($content -match "`r`n") {
        Write-Host "  INFO: CRLF line endings detected (normalized LF is recommended)" -ForegroundColor Cyan
        $infos++
    } else {
        Write-Host "  OK: Line endings OK (LF)" -ForegroundColor Green
    }
    
    # 3. Basic YAML validation (check for required keys)
    $yaml = Get-Content $file.FullName -Raw
    if ($yaml -notmatch "(?m)^name:\s*.+$") {
        Write-Host "  FAIL: Missing 'name:' key" -ForegroundColor Red
        $errors++
    }
    if ($yaml -notmatch "(?m)^on:\s*$") {
        Write-Host "  FAIL: Missing 'on:' trigger block" -ForegroundColor Red
        $errors++
    }
    if ($yaml -notmatch "(?m)^jobs:\s*$") {
        Write-Host "  FAIL: Missing 'jobs:' block" -ForegroundColor Red
        $errors++
    }
    
    # 4. Check for common YAML errors
    if ($yaml -match "\t") {
        Write-Host "  FAIL: Tabs detected (YAML requires spaces)" -ForegroundColor Red
        $errors++
    }
    
}

if ($errors -gt 0) {
    Write-Host "`nFAIL: Validation failed with $errors errors" -ForegroundColor Red
    exit 1
} else {
    if ($infos -gt 0) {
        Write-Host "`nINFO: Validation passed with $infos non-blocking formatting notices" -ForegroundColor Cyan
    }
    Write-Host "`nOK: All workflow files validated successfully" -ForegroundColor Green
    exit 0
}
