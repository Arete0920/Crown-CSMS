$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedRunId = "25528614282"
$ExpectedRunNumber = "270"
$ExpectedSha = "500ec09461d583eaf309a852df16d510fb334c81"
$ExpectedTag = "prod-deploy-20260507-orderfix-195608"

$ScriptPath = "scripts\release\35_create_claude_second_opinion_pack.ps1"
$PackDir = "audit-artifacts\prod-run-270-orderfix-verification\claude-second-opinion"
$ZipPath = "audit-artifacts\prod-run-270-orderfix-verification\claude-second-opinion.zip"

$ReportPath = Join-Path $PackDir "00_CLAUDE_PACK_VALIDATION_REPORT.md"
$ManifestPath = Join-Path $PackDir "00_CLAUDE_PACK_SHA256_MANIFEST.txt"

$RequiredFiles = @(
  "10_authoritative_capture_20260508_0023Z.txt",
  "99_VERIFICATION_REPORT.md",
  "99_verification_result.json",
  "RELEASE_AUTHORITY_95_PROOF_SNAPSHOT_20260506.md",
  "CLAUDE_PROMPT_MAIN.txt",
  "CLAUDE_PROMPT_RED_TEAM.txt",
  "CLAUDE_SECOND_OPINION_RUNBOOK.md"
)

function Mark {
  param([bool]$Ok)
  if ($Ok) { return "PASS" }
  return "FAIL"
}

function Test-FileContains {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Needle
  )

  if (-not (Test-Path $Path)) {
    return $false
  }

  $text = Get-Content -Raw -Path $Path -ErrorAction Stop
  return ($text.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
}

$GeneratedAt = (Get-Date).ToString("o")

$Checks = [ordered]@{}

$Checks["pack_builder_script_exists"] = Test-Path $ScriptPath
$Checks["pack_directory_exists"] = Test-Path $PackDir
$Checks["pack_zip_exists"] = Test-Path $ZipPath

foreach ($file in $RequiredFiles) {
  $Checks["required_file_exists::$file"] = Test-Path (Join-Path $PackDir $file)
}

$AllPackFiles = @()
if (Test-Path $PackDir) {
  $AllPackFiles = Get-ChildItem -Path $PackDir -File |
    Where-Object { $_.Name -notin @("00_CLAUDE_PACK_SHA256_MANIFEST.txt", "00_CLAUDE_PACK_VALIDATION_REPORT.md") } |
    Sort-Object Name
}

if ($AllPackFiles.Count -gt 0) {
  $AllPackFiles |
    ForEach-Object {
      $hash = Get-FileHash -Algorithm SHA256 -Path $_.FullName
      "{0}  {1}" -f $hash.Hash, $_.Name
    } |
    Out-File -FilePath $ManifestPath -Encoding utf8
}

$EvidenceFiles = @(
  (Join-Path $PackDir "10_authoritative_capture_20260508_0023Z.txt"),
  (Join-Path $PackDir "99_VERIFICATION_REPORT.md"),
  (Join-Path $PackDir "99_verification_result.json")
)

$CombinedEvidence = ""
foreach ($file in $EvidenceFiles) {
  if (Test-Path $file) {
    $CombinedEvidence += "`n===== $file =====`n"
    $CombinedEvidence += Get-Content -Raw -Path $file
  }
}

$Checks["evidence_contains_expected_run_id"] = ($CombinedEvidence.IndexOf($ExpectedRunId, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
$Checks["evidence_contains_expected_sha"] = ($CombinedEvidence.IndexOf($ExpectedSha, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
$Checks["evidence_contains_expected_tag"] = ($CombinedEvidence.IndexOf($ExpectedTag, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
$Checks["evidence_mentions_run_number_270"] = ($CombinedEvidence.IndexOf($ExpectedRunNumber, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
$Checks["main_prompt_exists_and_mentions_release_gate"] = Test-FileContains (Join-Path $PackDir "CLAUDE_PROMPT_MAIN.txt") "release"
$Checks["red_team_prompt_exists_and_mentions_red_team"] = Test-FileContains (Join-Path $PackDir "CLAUDE_PROMPT_RED_TEAM.txt") "red"
$Checks["runbook_exists_and_mentions_acceptance"] = Test-FileContains (Join-Path $PackDir "CLAUDE_SECOND_OPINION_RUNBOOK.md") "acceptance"

$reportFile = Join-Path $PackDir "99_VERIFICATION_REPORT.md"
$reportText = if (Test-Path $reportFile) { Get-Content -Raw -Path $reportFile } else { "" }

# Guardrails: keep technical closure scoped and prevent stale degraded lineage references.
$Checks["verification_report_has_scope_boundary"] = ($reportText.IndexOf("Scope Boundary", [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
$Checks["verification_report_denies_auto_governance_close"] =
  (($reportText.IndexOf("does not imply automatic", [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
   ($reportText.IndexOf("does not independently close", [System.StringComparison]::OrdinalIgnoreCase) -ge 0))
$Checks["technical_artifacts_do_not_reference_old_run_25526965033"] = ($CombinedEvidence.IndexOf("25526965033", [System.StringComparison]::OrdinalIgnoreCase) -lt 0)
$Checks["technical_artifacts_do_not_reference_old_sha_c7ab432"] = ($CombinedEvidence.IndexOf("c7ab432", [System.StringComparison]::OrdinalIgnoreCase) -lt 0)

$ZipHash = ""
$ZipSize = ""
if (Test-Path $ZipPath) {
  $ZipHash = (Get-FileHash -Algorithm SHA256 -Path $ZipPath).Hash
  $ZipSize = (Get-Item $ZipPath).Length
}

$AllPass = $true
foreach ($entry in $Checks.GetEnumerator()) {
  if (-not [bool]$entry.Value) {
    $AllPass = $false
  }
}

$Rows = New-Object System.Collections.Generic.List[string]
foreach ($entry in $Checks.GetEnumerator()) {
  $Rows.Add("| $($entry.Key) | $(Mark ([bool]$entry.Value)) |")
}

$Overall = Mark $AllPass

$Report = @"
# Claude Second-Opinion Pack Validation

Generated: $GeneratedAt

## Verdict

**$Overall**

## Expected production proof target

| Field | Value |
|---|---|
| Run number | $ExpectedRunNumber |
| Run ID | $ExpectedRunId |
| Commit SHA | $ExpectedSha |
| Deploy tag | $ExpectedTag |

## Package paths

| Item | Path |
|---|---|
| Pack builder script | $ScriptPath |
| Package directory | $PackDir |
| Package zip | $ZipPath |
| SHA256 manifest | $ManifestPath |

## Zip

| Field | Value |
|---|---|
| Exists | $(Test-Path $ZipPath) |
| Size bytes | $ZipSize |
| SHA256 | $ZipHash |

## Checks

| Check | Result |
|---|---:|
$($Rows -join "`n")

## Decision rule

PASS means the Claude review package is internally complete enough to upload for second-opinion review.

FAIL means do not send the package yet. Fix the missing file or missing lineage evidence first.
"@

if (-not (Test-Path $PackDir)) {
  throw "Pack directory does not exist: $PackDir"
}

$Report | Out-File -FilePath $ReportPath -Encoding utf8

Write-Host ""
Write-Host "============================================================"
Write-Host "CLAUDE PACK VALIDATION: $Overall"
Write-Host "Report: $ReportPath"
Write-Host "Manifest: $ManifestPath"
Write-Host "Zip SHA256: $ZipHash"
Write-Host "============================================================"
Write-Host ""

Get-Content $ReportPath

if (-not $AllPass) {
  throw "Claude second-opinion pack validation failed. Open $ReportPath."
}
