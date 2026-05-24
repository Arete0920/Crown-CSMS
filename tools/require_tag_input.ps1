param(
  [Parameter(Mandatory=$true)][string]$Tag
)

Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"

function Fail($msg) { Write-Host "FAIL: $msg" -ForegroundColor Red; exit 1 }
function Ok($msg)   { Write-Host "OK: $msg" -ForegroundColor Green }

if (-not $Tag.Trim()) { Fail "Missing required input: tag" }

# Make sure tags are available
git fetch --tags --force | Out-Null

# Validate tag exists locally after fetch
$sha = (git rev-list -n 1 $Tag 2>$null).Trim()
if (-not $sha) { Fail "Tag '$Tag' not found in repository (after fetch)" }

Ok "Tag input present and resolves: $Tag -> $sha"
