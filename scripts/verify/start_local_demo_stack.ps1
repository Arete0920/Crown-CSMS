$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
python scripts/demo/start_heritage_local.py
exit $LASTEXITCODE
