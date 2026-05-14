#!/usr/bin/env powershell
# 40_open_logs.ps1 - Open and parse .failed.log files from .crown-audit

param(
    [Parameter(Mandatory=$false)]
    [string]$LogDir = ".crown-audit",

    [Parameter(Mandatory=$false)]
    [int]$MaxFiles = 10
)

$ErrorActionPreference = "Stop"

Write-Host "Scanning for .failed.log files in $LogDir..." -ForegroundColor Cyan
Write-Host ""

# Find .failed.log files
$logFiles = @()
if (Test-Path $LogDir) {
    $logFiles = Get-ChildItem $LogDir -Recurse -Filter "*.failed.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxFiles
}

if ($logFiles.Count -eq 0) {
    Write-Host "No .failed.log files found in $LogDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($logFiles.Count) .failed.log files:" -ForegroundColor Green
Write-Host ""

foreach ($file in $logFiles) {
    Write-Host "─────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "File: $($file.Name)" -ForegroundColor Cyan
    Write-Host "Path: $($file.DirectoryName)" -ForegroundColor Gray
    Write-Host "Size: $($file.Length) bytes" -ForegroundColor Gray
    Write-Host "Modified: $($file.LastWriteTime)" -ForegroundColor Gray
    Write-Host ""

    # Extract error signature (first line starting with ERROR or FAILED)
    $content = Get-Content $file.FullName -First 50
    $errorLine = $content | Where-Object { $_ -match "ERROR|FAILED|EXCEPTION" } | Select-Object -First 1

    if ($errorLine) {
        Write-Host "Error: $errorLine" -ForegroundColor Red
    }

    Write-Host ""
}

Write-Host "─────────────────────────────────────────" -ForegroundColor Gray
Write-Host "Scan complete." -ForegroundColor Green
