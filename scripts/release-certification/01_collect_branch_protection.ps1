param(
  [string]$OutputDir,
  [string]$RepoSlug = "Arete0920/Crown-CSMS",
  [switch]$Skip
)

$ErrorActionPreference = "Stop"

$nativePreferenceVar = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
$hadNativePreference = ($null -ne $nativePreferenceVar)
$oldNativePreference = if ($hadNativePreference) { [bool]$nativePreferenceVar.Value } else { $false }
if ($hadNativePreference) {
  $global:PSNativeCommandUseErrorActionPreference = $false
}

$outJson = Join-Path $OutputDir "01_branch_protection.json"
$outTxt  = Join-Path $OutputDir "01_branch_protection_manual.txt"

if ($Skip) {
  "Skipped by operator." | Out-File $outTxt -Encoding utf8
  return
}

function Invoke-GhApiCapture {
  param([string]$Path)

  $result = [ordered]@{
    ExitCode = 0
    Text = ""
  }

  $prevErrorActionPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Stop"
    $response = & gh api $Path 2>&1
    $result.ExitCode = $LASTEXITCODE
    $result.Text = ($response | Out-String).Trim()
  } catch {
    $result.ExitCode = if ($LASTEXITCODE -ne 0) { $LASTEXITCODE } else { 1 }
    $result.Text = ($_ | Out-String).Trim()
  } finally {
    $ErrorActionPreference = $prevErrorActionPreference
  }

  return $result
}

try {
  if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required for branch protection export."
  }

  $protection = Invoke-GhApiCapture "/repos/$RepoSlug/branches/main/protection"
  $protectionResponse = $protection.Text
  $protectionExitCode = $protection.ExitCode

  if ($protectionExitCode -eq 0) {
    $protectionResponse | Out-File $outJson -Encoding utf8
  } else {
    $protectionErrorText = $protectionResponse
    $isDetailsNotFound = $protectionErrorText -match "(?i)(HTTP\s+404|404\s+Not\s+Found|Not\s+Found)"

    if (-not $isDetailsNotFound) {
      throw "gh api branch protection export failed: $protectionErrorText"
    }

    $branch = Invoke-GhApiCapture "/repos/$RepoSlug/branches/main"
    $branchResponse = $branch.Text
    $branchExitCode = $branch.ExitCode
    $branchInfo = $null
    if ($branchExitCode -eq 0 -and $branchResponse) {
      $branchInfo = $branchResponse | ConvertFrom-Json
    }

    $isProtected = $null -ne $branchInfo -and ($branchInfo.protected -eq $true)
    if ($isProtected) {
      # Branch metadata confirms protection; proceed with fallback evidence only for the known 404 details-endpoint case.
      [ordered]@{
        retrieval_mode = "fallback_branch_metadata"
        branch = "main"
        branch_protected = $true
        details_endpoint_error = $protectionErrorText
        note = "Detailed protection export returned 404 in this token/context; branch metadata still confirms protection."
      } | ConvertTo-Json -Depth 5 | Out-File $outJson -Encoding utf8
    } else {
      throw "gh api branch protection export failed and branch metadata did not confirm protection: $protectionErrorText"
    }
  }
} finally {
  if ($hadNativePreference) {
    $global:PSNativeCommandUseErrorActionPreference = $oldNativePreference
  }
}

@"
MANUAL REQUIRED
1. Open GitHub > Settings > Branches > main
2. Capture a screenshot showing:
   - required checks
   - include administrators
   - force pushes disabled
   - deletions disabled
   - linear history
   - conversation resolution
3. Save screenshot as:
   $OutputDir\01_branch_protection_screenshot.png

OPTIONAL EXTRA
- Capture a PR blocked by CodeQL
- Capture a PR blocked by dependency audit
"@ | Out-File $outTxt -Encoding utf8
