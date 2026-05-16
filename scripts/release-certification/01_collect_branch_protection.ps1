param(
  [string]$OutputDir,
  [string]$RepoSlug = "tcmegahan/Crown2026",
  [switch]$Skip
)

$ErrorActionPreference = "Stop"

$outJson = Join-Path $OutputDir "01_branch_protection.json"
$rulesetsJson = Join-Path $OutputDir "01_branch_rulesets.json"
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
  # Some repos enforce governance with rulesets instead of legacy branch protection.
  gh api "/repos/$RepoSlug/rulesets" > $rulesetsJson
  if ($LASTEXITCODE -ne 0) {
    throw "gh api branch protection export failed"
  }

  $rulesets = Get-Content $rulesetsJson -Raw | ConvertFrom-Json
  $activeBranchRulesets = @($rulesets | Where-Object {
    $_.target -eq "branch" -and $_.enforcement -eq "active"
  })

  if ($activeBranchRulesets.Count -eq 0) {
    throw "No active branch governance found (branch protection missing and no active branch rulesets)."
  }

  [pscustomobject]@{
    mode = "rulesets"
    repo = $RepoSlug
    branch_protection = "missing"
    active_branch_rulesets = $activeBranchRulesets | Select-Object id, name, enforcement, target
  } | ConvertTo-Json -Depth 6 | Out-File $outJson -Encoding utf8
}

@"
MANUAL REQUIRED
1. Open GitHub > Settings > Branches or Rulesets
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
