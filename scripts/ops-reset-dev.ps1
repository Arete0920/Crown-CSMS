param(
  [Parameter(Mandatory=$true)]
  [string]$SchoolId
)

$ErrorActionPreference="Stop"
$repo = (gh repo view --json nameWithOwner --jq '.nameWithOwner').Trim()

# Trigger workflow
gh workflow run ops-reset-dev.yml --repo $repo --field school_id="$SchoolId" | Out-Host

Start-Sleep -Seconds 2
"Latest runs:" | Write-Host
gh run list --repo $repo --limit 5 | Out-Host

"Open the latest run in browser:" | Write-Host
gh run view --repo $repo --web
