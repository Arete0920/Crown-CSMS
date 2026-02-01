# Validate workflow files before commit
# Run this before pushing any .github/workflows changes

$ErrorActionPreference = "Stop"

Write-Host "🔍 Validating workflow files..." -ForegroundColor Cyan

$workflowDir = ".github\workflows"
$files = Get-ChildItem $workflowDir -Filter *.yml

$errors = 0

foreach ($file in $files) {
    Write-Host "`nChecking $($file.Name)..." -ForegroundColor Yellow
    
    # 1. Check encoding (should be UTF8 without BOM)
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Write-Host "  ❌ UTF8-BOM detected (should be UTF8 no-BOM)" -ForegroundColor Red
        $errors++
    } else {
        Write-Host "  ✅ Encoding OK (UTF8 no-BOM)" -ForegroundColor Green
    }
    
    # 2. Check for CRLF (should be LF only for GitHub Actions)
    $content = Get-Content $file.FullName -Raw
    if ($content -match "`r`n") {
        Write-Host "  ⚠️  CRLF line endings detected (GitHub prefers LF)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ Line endings OK (LF)" -ForegroundColor Green
    }
    
    # 3. Basic YAML validation (check for required keys)
    $yaml = Get-Content $file.FullName -Raw
    if ($yaml -notmatch "(?m)^name:\s*.+$") {
        Write-Host "  ❌ Missing 'name:' key" -ForegroundColor Red
        $errors++
    }
    if ($yaml -notmatch "(?m)^on:\s*$") {
        Write-Host "  ❌ Missing 'on:' trigger block" -ForegroundColor Red
        $errors++
    }
    if ($yaml -notmatch "(?m)^jobs:\s*$") {
        Write-Host "  ❌ Missing 'jobs:' block" -ForegroundColor Red
        $errors++
    }
    
    # 4. Check for common YAML errors
    if ($yaml -match "\t") {
        Write-Host "  ❌ Tabs detected (YAML requires spaces)" -ForegroundColor Red
        $errors++
    }
    
    # 5. Check indentation consistency
    $lines = $yaml -split "`n"
    $indentPattern = @{}
    foreach ($line in $lines) {
        if ($line -match "^(\s+)") {
            $indent = $matches[1].Length
            $indentPattern[$indent] = $true
        }
    }
    $indents = $indentPattern.Keys | Sort-Object
    if ($indents -and ($indents[0] -ne 2 -or ($indents.Count -gt 1 -and $indents[1] -ne 4))) {
        Write-Host "  ⚠️  Non-standard indentation (should be 2-space)" -ForegroundColor Yellow
    }
}

if ($errors -gt 0) {
    Write-Host "`n❌ Validation failed with $errors errors" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n✅ All workflow files validated successfully" -ForegroundColor Green
    exit 0
}
