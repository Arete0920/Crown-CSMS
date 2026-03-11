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

"Latest run URL:" | Write-Host
$latestUrl = (gh run list --repo $repo --limit 1 --json url --jq '.[0].url').Trim()
if ($latestUrl) {
  Write-Host $latestUrl
}
