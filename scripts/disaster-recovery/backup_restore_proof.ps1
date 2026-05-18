#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$OUT = "audit-artifacts/disaster-recovery/$STAMP"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

"Generated: $(Get-Date -Format o)" | Out-File "$OUT/DR_PROOF.md"
"Purpose: backup/restore proof scaffold for Crown2026." | Out-File "$OUT/DR_PROOF.md" -Append

if (-not $env:DATABASE_URL) {
  "STATUS: SKIPPED - DATABASE_URL not set." | Out-File "$OUT/DR_PROOF.md" -Append
  Write-Host "DATABASE_URL not set. DR scaffold generated but restore not executed."
  exit 0
}

$backupFile = "$OUT/crown_backup.dump"

pg_dump $env:DATABASE_URL -Fc -f $backupFile

if (-not (Test-Path $backupFile)) {
  throw "Backup file was not created."
}

"STATUS: BACKUP_CREATED" | Out-File "$OUT/DR_PROOF.md" -Append
"BACKUP_FILE: $backupFile" | Out-File "$OUT/DR_PROOF.md" -Append
"SIZE_BYTES: $((Get-Item $backupFile).Length)" | Out-File "$OUT/DR_PROOF.md" -Append

Write-Host "Backup proof complete: $OUT"
