# Secret Rotation Runbook

**WHEN TO ROTATE**: Immediately if any secret appears in:
- Chat logs / screenshots
- PR text / commit messages
- Terminal output shared externally
- Unencrypted storage (clipboard, temp files)

**TRIGGER**: Any exposure = immediate rotation (no exceptions)

---

## 1. Generate New Secrets

```powershell
# Generate strong random passwords (run locally)
function New-Secret {
    param([int]$Length = 24)
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()'
    -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

$newDbPassword = "CrownPG2026Rotated$(Get-Date -Format 'MMdd')!$(New-Secret -Length 12)"
$newOpsSecret = "DevOpsSecret_Crown2026_Rotated_$(Get-Date -Format 'yyyyMMdd')_$(New-Secret -Length 20)"
$newCiPassword = "CrownCiRotated$(Get-Date -Format 'MMdd')!$(New-Secret -Length 12)"

# Display (DO NOT PASTE TO CHAT - save to local.secrets.ps1 manually)
Write-Host "NEW DB PASSWORD:" $newDbPassword
Write-Host "NEW OPS SECRET:" $newOpsSecret
Write-Host "NEW CI PASSWORD:" $newCiPassword
```

---

## 2. Rotate Database Password

```powershell
# Update Postgres server admin password
az postgres flexible-server update `
  --resource-group crown-rg `
  --name crown-pg-dev `
  --admin-password "<NEW_DB_PASSWORD>"

# Expected: state: Ready
```

---

## 3. Update Azure App Service

```powershell
# Update DATABASE_URL
$newDatabaseUrl = "postgresql://crownpgadmin:<NEW_DB_PASSWORD>@crown-pg-dev.postgres.database.azure.com:5432/crown2026_dev?sslmode=require"

az webapp config appsettings set `
  --name crown-api-dev `
  --resource-group crown-rg `
  --settings DATABASE_URL="$newDatabaseUrl"

# Update OPS secrets
az webapp config appsettings set `
  --name crown-api-dev `
  --resource-group crown-rg `
  --settings `
    DEV_OPS_SECRET="<NEW_OPS_SECRET>" `
    CROWN_OPS_SECRET="<NEW_OPS_SECRET>" `
    CI_SMOKE_PASSWORD="<NEW_CI_PASSWORD>"

# Restart app to pick up new connection pool
az webapp restart --name crown-api-dev --resource-group crown-rg
```

---

## 4. Update GitHub Actions Secrets

```powershell
# Update OPS secret used by workflows
gh secret set DEV_OPS_SECRET `
  --body "<NEW_OPS_SECRET>" `
  -R tcmegahan/Crown2026

# Verify
gh secret list -R tcmegahan/Crown2026
```

---

## 5. Update Local Environment

```powershell
# Edit local.secrets.ps1 (gitignored file)
notepad local.secrets.ps1

# Update these lines:
$env:PGPASSWORD = "<NEW_DB_PASSWORD>"
$env:DEV_OPS_SECRET = "<NEW_OPS_SECRET>"
$env:CROWN_OPS_SECRET = "<NEW_OPS_SECRET>"
$env:CI_SMOKE_PASSWORD = "<NEW_CI_PASSWORD>"
$env:DATABASE_URL = "postgresql://crownpgadmin:<NEW_DB_PASSWORD>@crown-pg-dev.postgres.database.azure.com:5432/crown2026_dev?sslmode=require"

# Reload
. .\local.secrets.ps1
```

---

## 6. Verification

```powershell
# Test DB connectivity (password entered interactively)
psql -h crown-pg-dev.postgres.database.azure.com `
     -U crownpgadmin `
     -d crown2026_dev `
     -c "SELECT 1;"
# Expected: 1 row returned

# Test OPS endpoint (use redacted output)
Invoke-RestMethod `
  -Uri "https://crown-api-dev.azurewebsites.net/api/v1/system/demo-reset/" `
  -Method POST `
  -Headers @{ "X-Admin-Ops-Secret"="<NEW_OPS_SECRET>"; "X-School-Id"="a5351136-98fe-4d48-add0-fa8f62d9ceff" } `
| Select-Object ok

# Expected: ok: True
```

---

## 7. Revoke Old Secrets (Verification)

**CRITICAL**: Old secrets are now invalid. Verify they no longer work:

```powershell
# Should FAIL with "Forbidden" or "401 Unauthorized"
Invoke-RestMethod `
  -Uri "https://crown-api-dev.azurewebsites.net/api/v1/system/demo-reset/" `
  -Method POST `
  -Headers @{ "X-Admin-Ops-Secret"="<OLD_OPS_SECRET>"; "X-School-Id"="..." }

# Expected: 401/403 error
```

---

## 8. Post-Rotation Checklist

- [ ] Database password rotated in Azure Postgres
- [ ] DATABASE_URL updated in App Service
- [ ] OPS secrets updated in App Service (both DEV_OPS_SECRET and CROWN_OPS_SECRET)
- [ ] CI password updated in App Service
- [ ] GitHub Actions DEV_OPS_SECRET updated
- [ ] local.secrets.ps1 updated with new values
- [ ] App Service restarted
- [ ] DB connectivity verified
- [ ] OPS endpoint verified (with new secret)
- [ ] Old secrets confirmed invalid
- [ ] **NEW CONVERSATION STARTED** (do not continue in contaminated thread)

---

## Emergency Contact

If rotation fails or exposes additional secrets:
1. Stop all work immediately
2. Rotate again with different patterns
3. Review all chat logs for additional exposures
4. Consider enabling Azure Key Vault + Managed Identity

---

## Prevention Checklist (Use Before Any Chat Session)

- [ ] Load secrets from `local.secrets.ps1` (never hardcode)
- [ ] Use `Invoke-SecureCommand` wrapper for Azure/DB commands
- [ ] Import `Redact.psm1` module at session start
- [ ] Paste commands only, never paste output
- [ ] Verify gitleaks is installed and pre-commit hook active
- [ ] Start new conversation for any ops work (never continue old threads)

---

**GOLDEN RULE**: If in doubt, rotate. Rotation is cheap; credential leaks are expensive.
