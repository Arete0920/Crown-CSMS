param(
  [Parameter(Mandatory=$true)]
  [string]$Tag,

  [Parameter(Mandatory=$true)]
  [string]$Message
)

$ErrorActionPreference = "Stop"

function Die($msg) {
  Write-Error $msg
  exit 1
}

# Must be on main
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "main") { Die "You must be on 'main' (current: $branch)." }

# Clean working tree
$porcelain = (git status --porcelain)
if ($porcelain) { Die "Working tree not clean. Commit/stash first." }

# Sync with origin/main
git fetch origin | Out-Null

$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse origin/main).Trim()
if ($local -ne $remote) {
  Die "Local main ($local) does not match origin/main ($remote). Run 'git pull' and try again."
}

# Tag must not already exist
$existing = (git tag --list $Tag).Trim()
if ($existing) { Die "Tag '$Tag' already exists." }

# Create annotated tag at HEAD and push
git tag -a $Tag -m $Message | Out-Null
git push origin $Tag | Out-Null

$line = (git show -s --decorate --oneline $Tag)
Write-Host "OK: $line"
