# Crown2026 Security Scripts

This directory contains PowerShell modules and scripts for safe credential handling.

---

## Quick Start

```powershell
# 1. Set up secrets file (ONCE)
Copy-Item local.secrets.ps1.example local.secrets.ps1
notepad local.secrets.ps1  # Fill in real values from Azure Portal

# 2. Load secrets in your session
. .\local.secrets.ps1

# 3. Import redaction module
Import-Module .\Scripts\Redact.psm1

# 4. Use secure wrappers for commands
.\Scripts\Invoke-SecureCommand.ps1 -Command "az webapp config appsettings list --name crown-api-dev --resource-group crown-rg"
```

---

## Files

### `ops/root_legacy/` (Moved root helper scripts)

These helper scripts were moved from repository root to reduce root clutter while keeping tooling available.

Examples now located here:
- `_list_urls.py`
- `check_a535_dupes.py`
- `clean_a535_admissions.py`
- `d3_smoke_tests.py`
- `fetch_real_payload.py`
- `get_grades_payload.py`
- `phase2_verification.py`
- `proof_b2_render.py`
- `verify_api_routing.py`
- `verify_invoices_schema.py`
- `verify_seed.py`
- `hex_audit.ps1`

Run from repo root, for example:

```bash
python scripts/ops/root_legacy/verify_api_routing.py
```

```powershell
./scripts/ops/root_legacy/hex_audit.ps1
```

### `Redact.psm1` (PowerShell Module)

**Functions**:
- `Redact [string]` - Removes secrets from text
- `Write-SafeHost [string]` - Auto-redacting Write-Host replacement
- `Copy-SafeClipboard [string]` - Copies text with redaction
- `Test-ContainsSecrets [string]` - Checks for secret patterns

**Usage**:
```powershell
Import-Module .\Scripts\Redact.psm1

# Redact a string
Redact "DB_PASSWORD=example_password_123"
# Returns: DB_PASSWORD=<REDACTED>

# Safe host output
Write-SafeHost "Token: Bearer abc123..." -ForegroundColor Green
# Displays: Token: Bearer <REDACTED>

# Safe clipboard copy
Get-Content .\log.txt | Copy-SafeClipboard
# Clipboard now contains redacted version

# Check for secrets
if (Test-ContainsSecrets $output) {
    Write-Host "WARNING: Contains secrets!"
}
```

---

### `Invoke-SecureCommand.ps1` (Command Wrapper)

**Purpose**: Execute commands with automatic output redaction

**Usage**:
```powershell
# Basic usage (auto-redacts output)
.\Scripts\Invoke-SecureCommand.ps1 -Command "az webapp config appsettings list --name crown-api-dev --resource-group crown-rg"

# Silent mode (no status messages)
.\Scripts\Invoke-SecureCommand.ps1 -Command "psql -c 'SELECT 1;'" -Silent

# Raw output (DANGEROUS - use only when certain no secrets)
.\Scripts\Invoke-SecureCommand.ps1 -Command "az group list" -AllowRawOutput
```

**What it redacts**:
- Passwords (any format)
- API keys / tokens
- Postgres connection strings
- Bearer tokens
- Crown-specific patterns (CrownPG*, DevOpsSecret_*, CrownCi*)

---

## No-Secrets Command Patterns

### ✅ SAFE - Paste these to chat
```powershell
# Check setting EXISTS (boolean only)
az webapp config appsettings list `
  --name crown-api-dev `
  --resource-group crown-rg `
  --query "[?name=='DATABASE_URL'] | length(@)" -o tsv
# Output: 0 or 1

# List setting NAMES only (no values)
az webapp config appsettings list `
  --name crown-api-dev `
  --resource-group crown-rg `
  --query "[].name" -o table

# Health check (non-sensitive fields)
curl.exe -s https://crown-api-dev.azurewebsites.net/api/health/ |
  ConvertFrom-Json |
  Select-Object ok,status,build_sha
```

### ❌ DANGEROUS - Never paste these
```powershell
# BAD: Dumps all settings with values
az webapp config appsettings list --name crown-api-dev --resource-group crown-rg

# BAD: Shows connection string
$env:DATABASE_URL

# BAD: Shows password
psql "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME}" -c "SELECT 1;"

# BAD: Logs token
$token = "Bearer abc..."
Write-Host "Token: $token"
```

---

## Integration with Chat/Copilot

### Before pasting to chat:
```powershell
# Option 1: Use secure wrapper
.\Scripts\Invoke-SecureCommand.ps1 -Command "az ..." | Copy-SafeClipboard

# Option 2: Redact manually
$output = az webapp config appsettings list --name crown-api-dev --resource-group crown-rg
Redact $output | Set-Clipboard

# Option 3: Paste command only, never output
# Share: "Ran: az webapp config appsettings list ..."
# Share: "Result: <REDACTED - VERIFIED LOCALLY>"
```

---

## Secret Rotation

If secrets are exposed:
1. **STOP** - Do not continue in same chat thread
2. Follow `ROTATE_SECRETS.md` runbook
3. Start new conversation after rotation
4. Verify old secrets invalid

---

## Pre-Commit Hook

Automatically scans staged files for secrets before commit.

**Setup** (already configured):
```bash
# Hook location
.git/hooks/pre-commit

# Test manually
gitleaks detect --no-git --staged
```

**If hook blocks commit**:
1. Remove secrets from staged files
2. Use `local.secrets.ps1` or env vars instead
3. Never use `git commit --no-verify` (bypasses safety)

---

## Maintenance

### Update Redaction Patterns
Edit `Scripts/Redact.psm1` to add new patterns:
```powershell
# Add to Redact function
$result = $result -replace 'NewPattern\d{4}', '<REDACTED>'
```

### Update Gitleaks Config
Edit `.gitleaks.toml` to add new rules:
```toml
[[rules]]
id = "new-pattern"
description = "New secret pattern"
regex = '''NewPattern\d{4}'''
tags = ["secret"]
```

---

## Troubleshooting

**"gitleaks not found"**
```powershell
winget install gitleaks.gitleaks
```

**"Module not found"**
```powershell
# Use full path
Import-Module C:\Users\JMega\OneDrive\Desktop\Crown2026\Scripts\Redact.psm1
```

**"Pre-commit hook not executing"**
```bash
# Make executable (Git Bash)
chmod +x .git/hooks/pre-commit

# Or reinstall
cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
# Then paste new content
```

---

## Reference

- Main guide: `ROTATE_SECRETS.md`
- Config: `.gitleaks.toml`
- Secrets template: `local.secrets.ps1.example`
- Pre-commit hook: `.git/hooks/pre-commit`
