param(
  [Parameter(Mandatory=$true)][ValidateSet("dev","prod")] [string]$Env,
  [Parameter(Mandatory=$true)] [string]$HealthUrl,
  [Parameter(Mandatory=$true)] [string]$ExpectedTag,
  [Parameter(Mandatory=$false)] [string]$ExpectedSha = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"

function Fail($msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
  exit 1
}

function Ok($msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

Write-Host "=== Deploy Integrity Proof ===" -ForegroundColor Cyan
Write-Host "env=$Env"
Write-Host "health=$HealthUrl"
Write-Host "expected_tag=$ExpectedTag"
if ($ExpectedSha) { Write-Host "expected_sha=$ExpectedSha" }

# --- Step 1: resolve expected tag -> sha (repo-local) ---
$tagSha = (git rev-list -n 1 $ExpectedTag 2>$null).Trim()
if (-not $tagSha) { Fail "Cannot resolve tag '$ExpectedTag' to a commit SHA (is the tag fetched?)" }
Ok "Tag resolves: $ExpectedTag -> $tagSha"

# --- Step 2: probe health endpoint ---
try {
  $resp = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 25
} catch {
  Fail "Health probe failed: $($_.Exception.Message)"
}

# Expected shape: contains build sha (commonly build_sha or sha)
$buildSha = ""
if ($null -ne $resp.build_sha) { $buildSha = [string]$resp.build_sha }
elseif ($null -ne $resp.sha)    { $buildSha = [string]$resp.sha }
elseif ($null -ne $resp.commit) { $buildSha = [string]$resp.commit }

if (-not $buildSha) {
  Fail "Health response missing build sha field (expected build_sha|sha|commit). Got keys: $(@($resp.PSObject.Properties.Name) -join ', ')"
}

Ok "Health reports build SHA: $buildSha"

# --- Step 3: compare tag sha to deployed sha ---
if ($buildSha -ne $tagSha) {
  Fail "Deployed SHA mismatch. Tag($ExpectedTag)=$tagSha but health reports $buildSha"
}
Ok "Deployed SHA matches expected tag SHA"

# --- Step 4: optional explicit expected sha check (belt & suspenders) ---
if ($ExpectedSha -and ($ExpectedSha -ne $buildSha)) {
  Fail "ExpectedSha mismatch: expected=$ExpectedSha actual=$buildSha"
}
if ($ExpectedSha) { Ok "ExpectedSha matches" }

Write-Host "=== PASS: Deploy integrity proof OK ===" -ForegroundColor Green
