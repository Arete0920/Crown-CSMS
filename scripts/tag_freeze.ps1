param(
  [Parameter(Mandatory=$true)]
  [string]$Label,

  [Parameter(Mandatory=$false)]
  [string]$Date = (Get-Date -Format "yyyy-MM-dd"),

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

# Build tag name
$tag = "freeze-$Date-$Label"

# Tag must not already exist
$existing = (git tag --list $tag).Trim()
if ($existing) { Die "Tag '$tag' already exists." }

# Create annotated tag at HEAD and push
git tag -a $tag -m $Message | Out-Null
git push origin $tag | Out-Null

$line = (git show -s --decorate --oneline $tag)
Write-Host "OK: $line"
