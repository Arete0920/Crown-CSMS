$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== CROWN2026 PUBLIC REPO HARDENING PASS ===" -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
  throw "This must be run from the Crown2026 repo root."
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$branch = "chore/public-repo-hardening-$stamp"
$auditDir = "audit-artifacts/public-repo-hardening/$stamp"
$backupDir = ".local-backups/public-repo-hardening/$stamp"

New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

"Repo: $repoRoot" | Out-File "$auditDir/00_run_context.txt"
"Timestamp: $stamp" | Add-Content "$auditDir/00_run_context.txt"
"Branch before: $(git branch --show-current)" | Add-Content "$auditDir/00_run_context.txt"
"Commit before: $(git rev-parse HEAD)" | Add-Content "$auditDir/00_run_context.txt"

Write-Host "Creating branch: $branch" -ForegroundColor Yellow
git checkout -b $branch

Write-Host "Updating .gitignore..." -ForegroundColor Yellow
if (-not (Test-Path ".gitignore")) {
  New-Item -ItemType File -Path ".gitignore" | Out-Null
}

$gitignoreAppend = @'

# Crown public repo hardening
.local-backups/
*.local
*.bak
*.backup
*.tmp
.env
.env.*
!.env.example
!.env.sample
.DS_Store
Thumbs.db
'@

$gitignoreText = Get-Content ".gitignore" -Raw
if ($gitignoreText -notmatch "\.local-backups/") {
  Add-Content ".gitignore" $gitignoreAppend
}

Write-Host "Removing unsafe public root debug/auth/seed scripts from HEAD..." -ForegroundColor Yellow
$unsafeRootFiles = @(
  "debug_auth.py",
  "test_custom_login.py",
  "seed_a535.py",
  "seed_a535_clean.py"
)

foreach ($file in $unsafeRootFiles) {
  if (Test-Path $file) {
    Copy-Item $file "$backupDir/$file" -Force
    git ls-files --error-unmatch $file 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      git rm -f $file
    } else {
      Remove-Item $file -Force
    }
  }
}

Write-Host "Creating safe dev templates..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "scripts/dev/examples" | Out-Null
New-Item -ItemType Directory -Force -Path "scripts/dev/seed" | Out-Null

@'
"""
CROWN manual auth check template.

Public-safe example only.
Do not hardcode emails, passwords, school IDs, bearer tokens, or tenant IDs.
Use environment variables.
"""

import os
import requests

BASE_URL = os.getenv("CROWN_BASE_URL", "http://127.0.0.1:8000")
EMAIL = os.getenv("CROWN_SANDBOX_EMAIL")
PASSWORD = os.getenv("CROWN_SANDBOX_PASSWORD")


def main() -> int:
    if not EMAIL or not PASSWORD:
        print(
            "Missing CROWN_SANDBOX_EMAIL or CROWN_SANDBOX_PASSWORD. "
            "Set them in your local environment. Do not commit credentials."
        )
        return 2

    response = requests.post(
        f"{BASE_URL.rstrip('/')}/api/token/",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=20,
    )

    print(f"Status: {response.status_code}")
    if response.ok:
        payload = response.json()
        safe_keys = sorted(k for k in payload.keys() if k.lower() not in {"access", "refresh", "token"})
        print(f"Authenticated. Response keys excluding tokens: {safe_keys}")
        return 0

    print(response.text[:1000])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content "scripts/dev/examples/manual_auth_check.example.py" -Encoding UTF8

@'
"""
CROWN sandbox seed template.

Public-safe example only.
Do not hardcode school IDs, tenant IDs, real people, credentials, or production data.
Convert this into a Django management command before production use.
"""

import os

SCHOOL_ID = os.getenv("CROWN_SANDBOX_SCHOOL_ID")
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE", "crown2026_config.settings")


def main() -> int:
    if not SCHOOL_ID:
        print("Missing CROWN_SANDBOX_SCHOOL_ID. Refusing to seed without explicit sandbox school context.")
        return 2

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

    print("Public-safe seed template.")
    print(f"Settings module: {DJANGO_SETTINGS_MODULE}")
    print(f"Sandbox school ID provided: {SCHOOL_ID[:8]}...")
    print("Add tenant-scoped sandbox seed logic here or convert to a Django management command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content "scripts/dev/seed/seed_sandbox_template.py" -Encoding UTF8

Write-Host "Creating .env.example..." -ForegroundColor Yellow
@'
# CROWN local development environment example
# Copy to .env locally. Never commit real .env files.

DJANGO_SETTINGS_MODULE=crown2026_config.settings
CROWN_ENVIRONMENT=local
CROWN_BASE_URL=http://127.0.0.1:8000

# Local-only sandbox testing
CROWN_SANDBOX_EMAIL=
CROWN_SANDBOX_PASSWORD=
CROWN_SANDBOX_SCHOOL_ID=

# Database
DATABASE_URL=

# Security
SECRET_KEY=
ALLOWED_HOSTS=127.0.0.1,localhost

# Microsoft 365 / Graph placeholders
MICROSOFT_TENANT_ID=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Payment / billing placeholders
PAYMENT_PROVIDER_SECRET=
'@ | Set-Content ".env.example" -Encoding UTF8

Write-Host "Backing up and replacing README.md..." -ForegroundColor Yellow
if (Test-Path "README.md") {
  Copy-Item "README.md" "$backupDir/README.before-public-hardening.md" -Force
}

@'
# CROWN

Christian School Management Solution

## Current public status

CROWN is currently treated as a release-candidate and sandbox-hardening codebase unless a later signed release note explicitly states otherwise.

Do not represent this repository as generally available production software until the release gates in this repository are green and current.

## Public repo rules

This is a public repository.

Never commit:
- passwords
- API keys
- bearer tokens
- refresh tokens
- real student data
- real family data
- real staff data
- real school financial data
- production .env files
- production database dumps
- private certificates
- tenant secrets
- Microsoft 365 client secrets

Sandbox data must be clearly labeled as sandbox data.

## Security

Use private security reporting. Do not open public issues for vulnerabilities. See SECURITY.md.

## Known limitations

See docs/KNOWN_LIMITATIONS.md.

## Public repo status

See docs/PUBLIC_REPO_STATUS.md.

## Release evidence

See docs/release/README.md.
'@ | Set-Content "README.md" -Encoding UTF8

Write-Host "Updating SECURITY.md..." -ForegroundColor Yellow
if (Test-Path "SECURITY.md") {
  Copy-Item "SECURITY.md" "$backupDir/SECURITY.before-public-hardening.md" -Force
}

@'
# Security Policy

CROWN handles school operations data and is designed for environments involving students, families, staff, communications, billing, and school records.

## Reporting a vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Report privately to the repository owner or designated security contact.

## Sensitive data rules

Never commit:
- passwords
- API keys
- tokens
- refresh tokens
- real student data
- real family data
- real staff data
- real financial data
- production .env files
- tenant secrets
- private certificates
- database dumps
- Microsoft 365 client secrets

## Public repository rule

All examples must use placeholders or environment variables. Sandbox credentials must not be committed even if they are non-production.

## Tenant isolation

Any vulnerability that can expose data across schools or tenants is treated as critical until proven otherwise.
'@ | Set-Content "SECURITY.md" -Encoding UTF8

Write-Host "Creating public repo docs..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "docs/release" | Out-Null
New-Item -ItemType Directory -Force -Path "docs/security" | Out-Null
New-Item -ItemType Directory -Force -Path "docs/governance" | Out-Null
New-Item -ItemType Directory -Force -Path "docs/dashboard" | Out-Null
New-Item -ItemType Directory -Force -Path "docs/engineering" | Out-Null

@'
# Public Repository Status

CROWN is public for transparency, review, and controlled development.

Current public posture:
- release candidate and sandbox hardening
- production GA not claimed from this file
- public data is sandbox/demo only
- sensitive data prohibited
'@ | Set-Content "docs/PUBLIC_REPO_STATUS.md" -Encoding UTF8

@'
# Known Limitations

Current known limitation categories:
- KPI cards must be connected to live APIs before production approval.
- KPI counts must reconcile with filtered source records.
- Route checks across source/review/dashboard must pass at required viewports.
- Accessibility and tenant isolation must pass automated checks.
'@ | Set-Content "docs/KNOWN_LIMITATIONS.md" -Encoding UTF8

@'
# Release Evidence Index

Only the current release index and signed release packet should be used for release decisions.

Required production proof includes backend tests, frontend tests, dependency and secret scan, tenant isolation, RBAC, routes and KPI source wiring, migrations, health checks, deploy checks, accessibility, responsive checks, and evidence bundle.
'@ | Set-Content "docs/release/README.md" -Encoding UTF8

@'
# GitHub Governance and Required Checks

Main branch should require pull request review, code owner review, resolved threads, fresh approval after push, and required checks.

Required checks should include public-repo-quality-gate, secret scan, test gates, tenant isolation, contract gates, route gates, and dashboard wiring gates.
'@ | Set-Content "docs/governance/GITHUB_REQUIRED_CHECKS.md" -Encoding UTF8

@'
# Dashboard Production Gate

The school administrator dashboard is not production-approved until every card and route is live-wired.

Each KPI must map to endpoint, permissions, tenant and year context, source records, review route, dashboard route, timestamp, and audit event.
'@ | Set-Content "docs/dashboard/DASHBOARD_PRODUCTION_GATE.md" -Encoding UTF8

@'
# Public Repository Hardening Notes

Completed by this pass:
- removed unsafe root scripts from HEAD
- added public-safe templates and env example
- hardened README and SECURITY
- added governance and dashboard gate docs
- added quality gate workflow and local audit script
'@ | Set-Content "docs/engineering/PUBLIC_REPO_HARDENING.md" -Encoding UTF8

Write-Host "Updating CODEOWNERS..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path ".github" | Out-Null
if (Test-Path ".github/CODEOWNERS") {
  Copy-Item ".github/CODEOWNERS" "$backupDir/CODEOWNERS.before-public-hardening" -Force
}

@'
* @tcmegahan

.github/** @tcmegahan
SECURITY.md @tcmegahan
README.md @tcmegahan
.env.example @tcmegahan
docs/security/** @tcmegahan
docs/governance/** @tcmegahan
docs/release/** @tcmegahan
docs/dashboard/** @tcmegahan
docs/engineering/** @tcmegahan
scripts/** @tcmegahan
contracts/** @tcmegahan
'@ | Set-Content ".github/CODEOWNERS" -Encoding UTF8

Write-Host "Hardening local ruleset JSON files where possible..." -ForegroundColor Yellow
function Set-JsonKeyRecursive {
  param(
    [Parameter(Mandatory=$true)] $Node,
    [Parameter(Mandatory=$true)] [string] $Key,
    [Parameter(Mandatory=$true)] $Value
  )

  if ($null -eq $Node) { return }

  if ($Node -is [System.Collections.IDictionary]) {
    foreach ($k in @($Node.Keys)) {
      if ($k -eq $Key) { $Node[$k] = $Value } else { Set-JsonKeyRecursive -Node $Node[$k] -Key $Key -Value $Value }
    }
  } elseif ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [string])) {
    foreach ($item in $Node) { Set-JsonKeyRecursive -Node $item -Key $Key -Value $Value }
  } elseif ($Node.PSObject.Properties.Count -gt 0) {
    foreach ($prop in $Node.PSObject.Properties) {
      if ($prop.Name -eq $Key) { $prop.Value = $Value } else { Set-JsonKeyRecursive -Node $prop.Value -Key $Key -Value $Value }
    }
  }
}

$rulesetFiles = @("ruleset_main.json", "ruleset_release.json", ".github/ruleset_main.json", ".github/ruleset_release.json") | Where-Object { Test-Path $_ }
foreach ($rf in $rulesetFiles) {
  Copy-Item $rf "$backupDir/$(Split-Path $rf -Leaf).before-public-hardening" -Force
  try {
    $json = Get-Content $rf -Raw | ConvertFrom-Json -Depth 100
    Set-JsonKeyRecursive -Node $json -Key "require_code_owner_review" -Value $true
    Set-JsonKeyRecursive -Node $json -Key "required_review_thread_resolution" -Value $true
    $json | ConvertTo-Json -Depth 100 | Set-Content $rf -Encoding UTF8
  } catch {
    "Could not parse or update $rf : $_" | Add-Content "$auditDir/01_ruleset_update_warnings.txt"
  }
}

Write-Host "Creating public repo quality gate workflow..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path ".github/workflows" | Out-Null

@'
name: public-repo-quality-gate

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  public-repo-quality-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Block unsafe root files
        shell: bash
        run: |
          set -euo pipefail
          forbidden=("debug_auth.py" "test_custom_login.py" "seed_a535.py" "seed_a535_clean.py")
          for f in "${forbidden[@]}"; do
            if [[ -e "$f" ]]; then
              echo "::error file=$f::Unsafe public root file exists"
              exit 1
            fi
          done

      - name: Block committed env and local backup files
        shell: bash
        run: |
          set -euo pipefail
          if git ls-files | grep -E '(^|/)\.env($|\.|/)'; then
            if git ls-files | grep -Ev '^\.env\.example$' | grep -E '(^|/)\.env($|\.|/)'; then
              echo "::error::Committed environment file detected"
              exit 1
            fi
          fi
          if git ls-files | grep -E '^\.local-backups/'; then
            echo "::error::.local-backups must never be committed"
            exit 1
          fi

      - name: Required public docs exist
        shell: bash
        run: |
          set -euo pipefail
          required=(
            "README.md"
            "SECURITY.md"
            "docs/PUBLIC_REPO_STATUS.md"
            "docs/KNOWN_LIMITATIONS.md"
            "docs/release/README.md"
            "docs/governance/GITHUB_REQUIRED_CHECKS.md"
            "docs/dashboard/DASHBOARD_PRODUCTION_GATE.md"
            "docs/engineering/PUBLIC_REPO_HARDENING.md"
            ".env.example"
            ".github/CODEOWNERS"
          )
          for f in "${required[@]}"; do
            [[ -s "$f" ]] || { echo "::error file=$f::Missing required file"; exit 1; }
          done
'@ | Set-Content ".github/workflows/public-repo-quality-gate.yml" -Encoding UTF8

Write-Host "Creating local public repo hardening audit script..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "scripts/audit" | Out-Null

@'
$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "audit-artifacts/public-repo-hardening-audit/$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
  param(
    [string] $Name,
    [bool] $Pass,
    [string] $Detail
  )

  $checks.Add([pscustomobject]@{
    Check = $Name
    Pass = $Pass
    Detail = $Detail
  })
}

$forbidden = @("debug_auth.py", "test_custom_login.py", "seed_a535.py", "seed_a535_clean.py")
foreach ($f in $forbidden) {
  Add-Check "Forbidden root file absent: $f" (-not (Test-Path $f)) $f
}

$required = @(
  "README.md",
  "SECURITY.md",
  "docs/PUBLIC_REPO_STATUS.md",
  "docs/KNOWN_LIMITATIONS.md",
  "docs/release/README.md",
  "docs/governance/GITHUB_REQUIRED_CHECKS.md",
  "docs/dashboard/DASHBOARD_PRODUCTION_GATE.md",
  "docs/engineering/PUBLIC_REPO_HARDENING.md",
  ".env.example",
  ".github/CODEOWNERS",
  ".github/workflows/public-repo-quality-gate.yml"
)
foreach ($f in $required) {
  Add-Check "Required file present: $f" (Test-Path $f) $f
}

$trackedEnv = git ls-files | Select-String -Pattern '(^|/)\.env($|\.|/)' | Where-Object { $_.Line -ne ".env.example" }
Add-Check "No tracked env files except .env.example" (-not $trackedEnv) (($trackedEnv | ForEach-Object Line) -join "; ")

$checks | Export-Csv "$out/public_repo_hardening_audit.csv" -NoTypeInformation
$failed = $checks | Where-Object { -not $_.Pass }

"=== PUBLIC REPO HARDENING AUDIT ===" | Out-File "$out/summary.txt"
"Generated: $stamp" | Add-Content "$out/summary.txt"
"Total: $($checks.Count)" | Add-Content "$out/summary.txt"
"Passed: $(($checks | Where-Object Pass).Count)" | Add-Content "$out/summary.txt"
"Failed: $($failed.Count)" | Add-Content "$out/summary.txt"

if ($failed) {
  Write-Host "Public repo hardening audit FAILED. See $out" -ForegroundColor Red
  exit 1
}

Write-Host "Public repo hardening audit PASSED. See $out" -ForegroundColor Green
'@ | Set-Content "scripts/audit/public_repo_hardening_audit.ps1" -Encoding UTF8

Write-Host "Running local public repo hardening audit..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File "scripts/audit/public_repo_hardening_audit.ps1"

Write-Host "Collecting git status..." -ForegroundColor Yellow
git status --short | Tee-Object -FilePath "$auditDir/02_git_status_after.txt"

Write-Host "Adding files..." -ForegroundColor Yellow
git add .gitignore .env.example README.md SECURITY.md .github/CODEOWNERS .github/workflows/public-repo-quality-gate.yml
if (Test-Path "docs/PUBLIC_REPO_STATUS.md") { git add docs/PUBLIC_REPO_STATUS.md }
if (Test-Path "docs/KNOWN_LIMITATIONS.md") { git add docs/KNOWN_LIMITATIONS.md }
if (Test-Path "docs/release/README.md") { git add docs/release/README.md }
if (Test-Path "docs/governance/GITHUB_REQUIRED_CHECKS.md") { git add docs/governance/GITHUB_REQUIRED_CHECKS.md }
if (Test-Path "docs/dashboard/DASHBOARD_PRODUCTION_GATE.md") { git add docs/dashboard/DASHBOARD_PRODUCTION_GATE.md }
if (Test-Path "docs/engineering/PUBLIC_REPO_HARDENING.md") { git add docs/engineering/PUBLIC_REPO_HARDENING.md }
if (Test-Path "scripts/dev/examples/manual_auth_check.example.py") { git add scripts/dev/examples/manual_auth_check.example.py }
if (Test-Path "scripts/dev/seed/seed_sandbox_template.py") { git add scripts/dev/seed/seed_sandbox_template.py }
if (Test-Path "scripts/audit/public_repo_hardening_audit.ps1") { git add scripts/audit/public_repo_hardening_audit.ps1 }
if (Test-Path "audit-artifacts/public-repo-hardening") { git add audit-artifacts/public-repo-hardening }
if (Test-Path "audit-artifacts/public-repo-hardening-audit") { git add audit-artifacts/public-repo-hardening-audit }
foreach ($rf in $rulesetFiles) { git add $rf }
foreach ($file in $unsafeRootFiles) { git add -u $file 2>$null }

$changes = git status --porcelain
if (-not $changes) {
  Write-Host "No changes detected. Nothing to commit." -ForegroundColor Yellow
} else {
  git commit -m "Harden public repository exposure and release governance"
}

Write-Host "Pushing branch to origin..." -ForegroundColor Yellow
git push -u origin $branch

Write-Host ""
Write-Host "=== COMPLETE ===" -ForegroundColor Green
Write-Host "Branch pushed: $branch"
Write-Host "Audit artifacts: $auditDir"
