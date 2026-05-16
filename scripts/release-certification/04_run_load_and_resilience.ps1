param(
  [string]$OutputDir,
  [string]$LoadHost = "",
  [switch]$Skip
)

$ErrorActionPreference = "Stop"

# Locust writes regular INFO logs to stderr; keep native stderr from failing the lane.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-LocustRun {
  param(
    [string[]]$Arguments,
    [string]$OutputPath,
    [string]$FailureMessage
  )

  $stderrPath = "$OutputPath.stderr"
  $proc = Start-Process -FilePath "locust" `
    -ArgumentList $Arguments `
    -RedirectStandardOutput $OutputPath `
    -RedirectStandardError $stderrPath `
    -NoNewWindow `
    -PassThru `
    -Wait

  if (Test-Path $stderrPath) {
    Get-Content $stderrPath | Add-Content $OutputPath
    Remove-Item $stderrPath -Force -ErrorAction SilentlyContinue
  }

  if ($proc.ExitCode -ne 0) {
    throw $FailureMessage
  }
}

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

$normalizedHost = if ($LoadHost -match "^https?://") { $LoadHost } else { "https://$LoadHost" }

if (-not (Test-Path "scripts/load/locustfile.py")) {
  throw "scripts/load/locustfile.py not found."
}

$installOut = Join-Path $OutputDir "04_locust_install.txt"
$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
python -m pip install locust *> $installOut
$pipExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorAction

if ($pipExitCode -ne 0) {
  throw "locust installation failed"
}
New-Item -ItemType Directory -Force -Path (Join-Path $OutputDir "load") | Out-Null

Invoke-LocustRun `
  -Arguments @(
    "-f", "scripts/load/locustfile.py",
    "--headless", "-u", "200", "-r", "20", "--run-time", "120s",
    "--host", $normalizedHost,
    "--html", (Join-Path $OutputDir "load/crown-load-smoke.html")
  ) `
  -OutputPath (Join-Path $OutputDir "04_load_smoke.txt") `
  -FailureMessage "locust smoke run failed"

Invoke-LocustRun `
  -Arguments @(
    "-f", "scripts/load/locustfile.py",
    "--headless", "-u", "200", "-r", "20", "--run-time", "180s",
    "--host", $normalizedHost,
    "--html", (Join-Path $OutputDir "load/crown-load-final.html"),
    "--csv", (Join-Path $OutputDir "load/crown-load-final")
  ) `
  -OutputPath (Join-Path $OutputDir "04_load_final.txt") `
  -FailureMessage "locust final run failed"

[pscustomobject]@{
  skipped = $false
  host    = $normalizedHost
} | ConvertTo-Json -Depth 4 | Out-File $outFile -Encoding utf8
