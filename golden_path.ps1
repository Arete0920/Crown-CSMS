param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Real = Join-Path $RepoRoot "tools\dev_scripts\golden_path.ps1"

if (!(Test-Path $Real)) { throw "Missing harness: $Real" }

# Run the real harness, forwarding parameters
& $Real -ApiBase $ApiBase -SkipSeed:$SkipSeed
