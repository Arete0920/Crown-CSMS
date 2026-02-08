param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern('^gate-[0-9]+(-[a-z0-9\-]+)?$')]
  [string]$GateTag,

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
$existing = (git tag --list $GateTag).Trim()
if ($existing) { Die "Tag '$GateTag' already exists." }

# Create annotated tag at HEAD and push
git tag -a $GateTag -m $Message | Out-Null
git push origin $GateTag | Out-Null

$line = (git show -s --decorate --oneline $GateTag)
Write-Host "OK: $line"
