<#
.SYNOPSIS
  Deterministic pytest proof capture — always produces a timestamped proof file.

.USAGE
  From repo root:
    .\tools\run_pytest_proof.ps1

.OUTPUT
  PYTEST_PROOF_<timestamp>.txt  — full output
  Exit code mirrors pytest exit code.
#>
$ErrorActionPreference = "Stop"

$ts  = Get-Date -Format "yyyyMMdd-HHmmss"
$log = "PYTEST_PROOF_$ts.txt"

Write-Host "== pytest proof capture -> $log ==" -ForegroundColor Cyan

# Run pytest; Tee-Object writes to file AND screen simultaneously.
& ".\.venv\Scripts\python.exe" -m pytest -q --tb=short *>&1 | Tee-Object -FilePath $log
$exit = $LASTEXITCODE

# Stamp the exit code at the bottom of the proof file.
"" | Out-File -FilePath $log -Append -Encoding utf8
"EXIT:$exit" | Out-File -FilePath $log -Append -Encoding utf8

# Show summary lines.
$summary = Select-String -Path $log -Pattern "passed|failed|error|warnings|skipped" |
           Select-Object -Last 5
Write-Host ""
Write-Host "---- pytest summary ----" -ForegroundColor Cyan
$summary | ForEach-Object { Write-Host $_.Line }
Write-Host "---- proof file: $log ----" -ForegroundColor Cyan

if ($exit -ne 0) {
    throw "pytest failed (exit $exit). See $log"
}
