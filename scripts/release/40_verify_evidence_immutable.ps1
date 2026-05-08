#!/usr/bin/env pwsh
<#
.SYNOPSIS
Verifies that all pilot evidence files are present and immutable (SHA256 checksums match)
.DESCRIPTION
Runs before gate meeting to confirm evidence freeze is intact
.OUTPUTS
Exit Code 0 = All evidence verified. Exit Code 1 = Evidence integrity failure
#>

param(
    [string]$EvidenceDir = ".",
    [string]$ManifestFile = "EVIDENCE_SHA256_MANIFEST.txt"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$requiredFiles = @(
    "00_SUMMARY.md",
    "EXECUTIVE_SUMMARY.md",
    "DELIVERABLES_SUMMARY.md",
    "99_STATUS.json",
    "AUDIT_DECISION.json",
    "GOVERNANCE_95_PROOF_SNAPSHOT_20260506.md"
)

Write-Host "=== EVIDENCE INTEGRITY VERIFICATION ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ' -AsUTC)"
Write-Host ""

$allPassed = $true
$verificationLog = @()

# Check all required files exist
Write-Host "Checking required files..." -ForegroundColor Yellow
foreach ($file in $requiredFiles) {
    $path = Join-Path $EvidenceDir $file
    if (Test-Path $path) {
        Write-Host "  ✓ $file found" -ForegroundColor Green
        $verificationLog += "✓ $file"
    }
    else {
        Write-Host "  ✗ $file MISSING" -ForegroundColor Red
        $allPassed = $false
        $verificationLog += "✗ $file MISSING"
    }
}

# Verify SHA256 checksums if manifest exists
$manifestPath = Join-Path $EvidenceDir $ManifestFile
if (Test-Path $manifestPath) {
    Write-Host ""
    Write-Host "Verifying SHA256 checksums..." -ForegroundColor Yellow
    
    $manifestContent = Get-Content $manifestPath -Raw
    $failedChecks = 0
    
    foreach ($line in @($manifestContent -split "`n")) {
        $line = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        
        $parts = $line -split "\s+"
        if ($parts.Count -lt 2) {
            continue
        }
        
        $expectedHash = $parts[0]
        $fileName = $parts[1..($parts.Count-1)] -join " "
        $filePath = Join-Path $EvidenceDir $fileName
        
        if (Test-Path $filePath) {
            $actualHash = (Get-FileHash $filePath -Algorithm SHA256).Hash
            if ($actualHash -eq $expectedHash) {
                Write-Host "  ✓ $fileName (hash verified)" -ForegroundColor Green
                $verificationLog += "✓ $fileName (SHA256 verified)"
            }
            else {
                Write-Host "  ✗ $fileName (HASH MISMATCH!)" -ForegroundColor Red
                Write-Host "     Expected: $expectedHash" -ForegroundColor Red
                Write-Host "     Actual:   $actualHash" -ForegroundColor Red
                $allPassed = $false
                $failedChecks++
                $verificationLog += "✗ $fileName (HASH MISMATCH)"
            }
        }
    }
    
    if ($failedChecks -gt 0) {
        Write-Host ""
        Write-Host "⚠️  Evidence integrity check FAILED" -ForegroundColor Red
        Write-Host "    $failedChecks file(s) have been modified since freeze" -ForegroundColor Red
    }
}
else {
    Write-Host ""
    Write-Host "⚠️  Manifest file not found: $ManifestFile" -ForegroundColor Yellow
    Write-Host "    Cannot verify checksums without manifest" -ForegroundColor Yellow
}

Write-Host ""
if ($allPassed) {
    Write-Host "✅ All evidence files verified as immutable" -ForegroundColor Green
    Write-Host "   Evidence freeze is intact and ready for gate meeting" -ForegroundColor Green
    
    # Save verification record
    $recordPath = Join-Path $EvidenceDir "EVIDENCE_VERIFICATION_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    Set-Content -Path $recordPath -Value ($verificationLog -join "`n")
    Write-Host ""
    Write-Host "   Verification record: $recordPath" -ForegroundColor Cyan
    
    exit 0
}
else {
    Write-Host "❌ Evidence integrity check FAILED" -ForegroundColor Red
    Write-Host "   Gate meeting CANNOT proceed" -ForegroundColor Red
    Write-Host "   Reason: One or more evidence files are missing or corrupted" -ForegroundColor Red
    
    exit 1
}
