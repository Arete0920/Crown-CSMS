$ErrorActionPreference = "Stop"
Set-Location "C:\w\crown_main_postmerge_verify"
$Root = "audit-artifacts\51x51-module-integrity"
$Latest = Get-ChildItem $Root -Directory |
    Where-Object { $_.Name -match "^\d{8}_\d{6}$" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Latest) {
    throw "No timestamped 51x51 audit folder found."
}

$RunPath = $Latest.FullName
$EvidencePath = Join-Path $RunPath "evidence"
$Transcript = Join-Path $RunPath "terminal_transcript.txt"
$EvidenceCount = if (Test-Path $EvidencePath) {
    (Get-ChildItem $EvidencePath -File -ErrorAction SilentlyContinue | Measure-Object).Count
} else {
    0
}

$HasExecutiveSummary = Test-Path (Join-Path $RunPath "00_EXECUTIVE_SUMMARY.md")
$HasStatusJson       = Test-Path (Join-Path $RunPath "99_STATUS.json")
$HasMatrix           = Test-Path (Join-Path $RunPath "01_51x51_MODULE_INTEGRITY_MATRIX.csv")
$HasFixMatrix        = Test-Path (Join-Path $RunPath "03_FIX_MATRIX.csv")

$TranscriptTail = ""
if (Test-Path $Transcript) {
    $TranscriptTail = (Get-Content $Transcript -Tail 80 -ErrorAction SilentlyContinue) -join "`n"
}

$Status = [ordered]@{
    decision = "NO-GO"
    gate = "136_crown_51x51_module_integrity_audit.ps1"
    complete = $false
    reason = "Authoritative 51x51 gate did not emit required final score artifacts."
    latest_run_path = $RunPath
    evidence_files = $EvidenceCount
    required_artifacts = [ordered]@{
        executive_summary = $HasExecutiveSummary
        status_json = $HasStatusJson
        module_integrity_matrix = $HasMatrix
        fix_matrix = $HasFixMatrix
    }
    pass = $null
    review = $null
    fail = $null
    strict_rule = "GO requires completed fresh 136 output with FAIL=0 and REVIEW=0."
    transcript_tail = $TranscriptTail
    generated_at = (Get-Date).ToString("s")
}

$OutJson = Join-Path $RunPath "99_STATUS_INCOMPLETE_NO_GO.json"
$OutMd   = Join-Path $RunPath "00_EXECUTIVE_SUMMARY_INCOMPLETE_NO_GO.md"

$Status | ConvertTo-Json -Depth 10 | Set-Content $OutJson -Encoding UTF8

@"
# 51x51 Integrity Gate — Incomplete NO-GO

## Decision

**NO-GO**

## Reason

The authoritative 136 gate did not emit the required final score artifacts.

## Latest Run

$RunPath

## Required Artifact Check

| Artifact | Present |
|---|---:|
| 00_EXECUTIVE_SUMMARY.md | $HasExecutiveSummary |
| 99_STATUS.json | $HasStatusJson |
| 01_51x51_MODULE_INTEGRITY_MATRIX.csv | $HasMatrix |
| 03_FIX_MATRIX.csv | $HasFixMatrix |

## Evidence Files Written

$EvidenceCount

## Strict Rule

GO requires a completed fresh 136 output with:
- FAIL = 0
- REVIEW = 0
- required final artifacts present

That standard was not met.

## Next Required Engineering Action

Implement deterministic fast/resumable evidence mode in `136_crown_51x51_module_integrity_audit.ps1`, then rerun until it emits final artifacts.
"@ | Set-Content $OutMd -Encoding UTF8

Write-Host "Incomplete NO-GO status written:"
Write-Host $OutJson
Write-Host $OutMd
