param(
  [Parameter(Mandatory=$true)]
  [string]$Tag,

  [Parameter(Mandatory=$true)]
  [string]$Message
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Die([string]$msg) {
  Write-Error $msg
  exit 1
}

# Must be in a git repo
try { git rev-parse --is-inside-work-tree | Out-Null } catch { Die "Not inside a git repository." }

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

# Tag must not already exist (strict)
git rev-parse -q --verify "refs/tags/$Tag" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { Die "Tag '$Tag' already exists." }

# Build canonical annotated message (audit trail)
$sha   = $local
$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$body = @"
Crown Canon Tag
type: spine
tag: $Tag
branch: $branch
sha: $sha
utc: $stamp
note: $Message
"@

# Create annotated tag at HEAD and push
git tag -a $Tag -m $body | Out-Null
git push origin $Tag | Out-Null

$line = (git show -s --decorate --oneline $Tag)
Write-Host "OK: $line"
