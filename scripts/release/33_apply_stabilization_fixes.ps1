$ErrorActionPreference = "Stop"

function Write-Utf8File {
    param([string]$Path,[string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Ensure-TextBlock {
    param([string]$Path,[string]$Needle,[string]$Block)
    if (-not (Test-Path $Path)) { return }
    $text = Get-Content $Path -Raw
    if ($text -notmatch [regex]::Escape($Needle)) {
        $text = $text.TrimEnd() + "`r`n`r`n" + $Block.Trim() + "`r`n"
        [System.IO.File]::WriteAllText((Resolve-Path $Path), $text, (New-Object System.Text.UTF8Encoding($false)))
    }
}

# 1) Ensure django-extensions is available to support show_urls in audit runs
$reqFiles = @("backend/requirements.txt","requirements.txt") | Where-Object { Test-Path $_ }
foreach ($file in $reqFiles) {
    $text = Get-Content $file -Raw
    if ($text -notmatch '(?im)^django-extensions([<>=].*)?$') {
        $append = if ($text.TrimEnd().Length -gt 0) { "`r`ndjango-extensions`r`n" } else { "django-extensions`r`n" }
        [System.IO.File]::WriteAllText((Resolve-Path $file), ($text + $append), (New-Object System.Text.UTF8Encoding($false)))
        Write-Host "Added django-extensions to $file"
    } else {
        Write-Host "django-extensions already present in $file"
    }
}

# 2) Ensure django_extensions is in INSTALLED_APPS for audit visibility
$settingsCandidates = Get-ChildItem -Recurse -File -Include settings.py 2>$null |
  Where-Object { $_.FullName -match "backend|crown2026_config|config|settings" } |
  Select-Object -ExpandProperty FullName -Unique

foreach ($settingsFile in $settingsCandidates) {
    Ensure-TextBlock -Path $settingsFile -Needle '"django_extensions"' -Block @'
INSTALLED_APPS = globals().get("INSTALLED_APPS", INSTALLED_APPS if "INSTALLED_APPS" in globals() else [])
if "django_extensions" not in INSTALLED_APPS:
    INSTALLED_APPS.append("django_extensions")
'@
}

# 3) Add a repo note for audit prerequisites
Write-Utf8File -Path "docs/release/AUDIT_PREREQUISITES.md" -Content @'
# AUDIT PREREQUISITES

## Required for a complete audit pack
- Working Python executable
- Installed backend requirements
- `django-extensions` installed and enabled in `INSTALLED_APPS`
- Authenticated GitHub CLI (`gh auth status`)
- Reachable health base URL, or local server on `127.0.0.1:8000`

## Branch protection note
Branch protection retrieval uses GitHub API access and may return `403` if the authenticated identity lacks permission. That cannot be fixed by repo code alone.
'@

# 4) Add a small helper to verify prerequisites before rerun
Write-Utf8File -Path "scripts/release/34a_verify_audit_prereqs.ps1" -Content @'
$ErrorActionPreference = "Continue"

Write-Host "=== PYTHON ==="
python --version 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "python not available" }

Write-Host "=== GITHUB CLI ==="
gh auth status

Write-Host "=== DJANGO MANAGE CHECK ==="
if (Test-Path "backend/manage.py") {
  python backend/manage.py check
  python backend/manage.py showmigrations
  python backend/manage.py help | Select-String "show_urls"
} elseif (Test-Path "manage.py") {
  python manage.py check
  python manage.py showmigrations
  python manage.py help | Select-String "show_urls"
} else {
  Write-Host "manage.py not found"
}
'@

Write-Host "Applied stabilization fixes."
