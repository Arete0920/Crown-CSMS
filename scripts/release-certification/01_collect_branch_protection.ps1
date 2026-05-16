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

gh api "/repos/$RepoSlug/branches/main/protection" > $outJson
if ($LASTEXITCODE -ne 0) {
  throw "gh api branch protection export failed"
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
