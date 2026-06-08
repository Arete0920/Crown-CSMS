param(
  [string]$OutputDir,
  [string]$RepoSlug = "tcmegahan/Crown2026",
  [switch]$Skip
)

$ErrorActionPreference = "Stop"

$outJson = Join-Path $OutputDir "01_branch_protection.json"
$outTxt  = Join-Path $OutputDir "01_branch_protection_manual.txt"

if ($Skip) {
  "Skipped by operator." | Out-File $outTxt -Encoding utf8
  return
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI (gh) is required for branch protection export."
}

$protectionResponse = & gh api "/repos/$RepoSlug/branches/main/protection" 2>&1
$protectionExitCode = $LASTEXITCODE

if ($protectionExitCode -eq 0) {
  $protectionResponse | Out-File $outJson -Encoding utf8
} else {
  $protectionErrorText = ($protectionResponse | Out-String).Trim()
  $isDetailsNotFound = $protectionErrorText -match "(?i)(HTTP\s+404|404\s+Not\s+Found|Not\s+Found)"

  if (-not $isDetailsNotFound) {
    throw "gh api branch protection export failed: $protectionErrorText"
  }

  $branchResponse = & gh api "/repos/$RepoSlug/branches/main" 2>$null
  $branchExitCode = $LASTEXITCODE
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
