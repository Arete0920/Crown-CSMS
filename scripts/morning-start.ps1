# Morning Start Script
# Single deterministic command to validate workspace state before starting work

$ErrorActionPreference = "Stop"

Write-Host "`n=== MORNING START: Validating Workspace ===" -ForegroundColor Cyan

# Fetch latest from all remotes
Write-Host "`n1. Fetching latest from remotes..." -ForegroundColor Yellow
git fetch --all --prune

# Show current status
Write-Host "`n2. Current workspace status:" -ForegroundColor Yellow
git status -sb

# Switch to resume branch and sync
Write-Host "`n3. Switching to spine/resume-morning-0205..." -ForegroundColor Yellow
git checkout spine/resume-morning-0205
git pull

# Verify we're on the correct branch (fail-fast safety check)
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "spine/resume-morning-0205") { 
    throw "Not on resume branch. Current: $branch" 
}

# Show HEAD commit
Write-Host "`n4. Current HEAD:" -ForegroundColor Yellow
$currentHead = git rev-parse HEAD
Write-Host "   Commit: $currentHead"

# Final status check
Write-Host "`n5. Branch status:" -ForegroundColor Yellow
git status -sb

# Display next steps
Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Green
Write-Host "1) Check open PRs: gh pr list --base spine/resume-morning-0205"
Write-Host "2) If continuing work on PR: git checkout <feature-branch>"
Write-Host "3) Run backend tests: cd backend; python -m pytest -q"
Write-Host "4) If tests green, you're ready to code."
Write-Host "`nREMEMBER: No coding until tests are green on your working branch!"
