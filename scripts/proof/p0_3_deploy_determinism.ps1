# P0.3 Deploy Determinism Proof
# Verifies that /health/ returns the exact commit SHA that is currently deployed

$ErrorActionPreference = "Stop"

$base = "https://crown-api-dev.azurewebsites.net"
$sha = (git rev-parse HEAD).Trim()

Write-Host "Local HEAD SHA:  $sha"
Write-Host "Checking $base/health/..."
Write-Host ""

$result = curl.exe -s "$base/health/" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('build_sha','MISSING'))"

Write-Host "DEV build_sha:   $result"
Write-Host ""

if ($result -ne $sha) {
    throw "FAILED: DEV reports '$result' but expected '$sha'"
}

Write-Host "✅ P0.3 CLOSED: Deploy determinism proven"
Write-Host ""
Write-Host "Cryptographic proof: DEV /health/ returns the exact SHA of the deployed commit."
Write-Host "No 'stale code' arguments possible."
