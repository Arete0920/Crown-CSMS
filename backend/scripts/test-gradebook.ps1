$ErrorActionPreference = "Stop"

# --- ENV DOCTRINE PRECHECK (fail fast) ---
try {
  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
  $py = (Join-Path $repoRoot ".venv\Scripts\python.exe")
  if (!(Test-Path $py)) {
    Write-Error "Missing repo venv python: .venv\Scripts\python.exe. Create with: py -3.12 -m venv .venv"
    exit 2
  }
} catch {
  Write-Error "Missing repo venv python: .venv\Scripts\python.exe. Create with: py -3.12 -m venv .venv"
  exit 2
}

$ver = & $py -V 2>&1
if ($ver -notmatch "Python 3.12\.") {
  Write-Error "Wrong Python detected ($ver). Canon requires Python 3.12.x. Rebuild venv: py -3.12 -m venv .venv"
  exit 2
}
# --- END PRECHECK ---

# Run from repo root or backend; normalize to backend/
if (Test-Path ".\backend") { Set-Location ".\backend" }

if (Test-Path $repoRoot) { Set-Location (Join-Path $repoRoot "backend") }

& $py -m pytest -q `
  gradebook\tests\test_gradebook_grid_v1.py `
  gradebook\tests\test_gradebook_grid_v2.py
