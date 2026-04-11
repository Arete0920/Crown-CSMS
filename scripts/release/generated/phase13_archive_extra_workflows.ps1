param([switch]$Apply)
$ErrorActionPreference = "Stop"
$repoRoot = (git rev-parse --show-toplevel).Trim()
$destRoot = Join-Path $repoRoot (".github\workflows\_disabled_review\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
if ($Apply) { New-Item -ItemType Directory -Force -Path $destRoot | Out-Null }
