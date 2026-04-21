param(
  [string]$OutputDir,
  [string]$LoadHost = "",
  [switch]$Skip
)

$ErrorActionPreference = "Stop"

$outFile = Join-Path $OutputDir "04_load_summary.json"
if ($Skip) {
  [pscustomobject]@{
    skipped = $true
    reason  = "Operator requested skip"
  } | ConvertTo-Json -Depth 4 | Out-File $outFile -Encoding utf8
  return
}

if ([string]::IsNullOrWhiteSpace($LoadHost)) {
  throw "LoadHost is required unless -SkipLoad is used."
}
if (-not (Test-Path "scripts/load/locustfile.py")) {
  throw "scripts/load/locustfile.py not found."
}

python -m pip install locust *> (Join-Path $OutputDir "04_locust_install.txt")
if ($LASTEXITCODE -ne 0) {
  throw "locust installation failed"
}
New-Item -ItemType Directory -Force -Path (Join-Path $OutputDir "load") | Out-Null

locust -f scripts/load/locustfile.py `
  --headless -u 200 -r 20 --run-time 120s `
  --host $LoadHost `
  --html (Join-Path $OutputDir "load/crown-load-smoke.html") `
  *> (Join-Path $OutputDir "04_load_smoke.txt")
if ($LASTEXITCODE -ne 0) {
  throw "locust smoke run failed"
}

locust -f scripts/load/locustfile.py `
  --headless -u 500 -r 50 --run-time 300s `
  --host $LoadHost `
  --html (Join-Path $OutputDir "load/crown-load-final.html") `
  --csv (Join-Path $OutputDir "load/crown-load-final") `
  *> (Join-Path $OutputDir "04_load_final.txt")
if ($LASTEXITCODE -ne 0) {
  throw "locust final run failed"
}

[pscustomobject]@{
  skipped = $false
  host    = $LoadHost
} | ConvertTo-Json -Depth 4 | Out-File $outFile -Encoding utf8
