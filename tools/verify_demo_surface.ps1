param(
  [ValidateSet("static")]
  [string]$Mode = "static"
)

$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
  exit 1
}

function Pass([string]$msg) {
  Write-Host "PASS: $msg" -ForegroundColor Green
}

# Resolve repo root from script location
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repo

$router = Join-Path $repo "frontend/dashboards/src/routes/router.jsx"
if (!(Test-Path $router)) { Fail "router.jsx not found at: $router" }

$routerTxt = Get-Content $router -Raw

# --- Tier-1 Route Contract ---
# Must contain: path: '/students/:id' and Student360Page referenced in that route.
if ($routerTxt -notmatch "path:\s*['""]\/students\/:id['""]") {
  Fail "Tier-1 route missing: path '/students/:id' in router.jsx"
}
Pass "Router contains /students/:id route"

if ($routerTxt -notmatch "Student360Page") {
  Fail "Student360Page not referenced in router.jsx (import or usage missing)"
}
Pass "Student360Page referenced in router.jsx"

# --- Backend graduation URL contract (static) ---
# We avoid relying on manage.py show_urls in CI here; instead we assert code presence.
# You can strengthen this later, but this catches the common "forgot to include urls.py" mistake.
$gradUrls = Join-Path $repo "backend/graduation/urls.py"
if (!(Test-Path $gradUrls)) { Fail "backend/graduation/urls.py not found (graduation app wiring missing)" }

$gradUrlsTxt = Get-Content $gradUrls -Raw
if ($gradUrlsTxt -notmatch "audit") {
  Fail "graduation/urls.py does not appear to define an audit route (pattern missing 'audit')"
}
Pass "graduation/urls.py contains 'audit' route pattern"

# Verify API version prefix is wired somewhere in backend urls (best-effort static check)
$rootUrls = Join-Path $repo "backend/crown_api/urls.py"
if (!(Test-Path $rootUrls)) {
  # fallback common alt
  $rootUrls = Join-Path $repo "backend/config/urls.py"
}
if (!(Test-Path $rootUrls)) { Fail "Could not find backend root urls.py (expected backend/crown_api/urls.py or backend/config/urls.py)" }

$rootUrlsTxt = Get-Content $rootUrls -Raw
if ($rootUrlsTxt -notmatch "graduation") {
  Fail "Backend root urls.py does not reference 'graduation' (graduation urls may not be included)"
}
Pass "Backend root urls.py references 'graduation'"

Write-Host ""
Write-Host "DEMO SURFACE STATIC GATE: ALL CHECKS PASSED" -ForegroundColor Cyan
exit 0
