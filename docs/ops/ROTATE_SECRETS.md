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
# Generate values in your approved secret manager or local secure store.
# Do not print secrets to terminal and do not paste secrets into chat.
$newDbPassword = "<NEW_DB_PASSWORD>"
$newOpsSecret = "<NEW_OPS_SECRET>"
$newCiPassword = "<NEW_CI_PASSWORD>"
```

---

## 2. Rotate Database Password

```powershell
# Update Postgres server admin password
az postgres flexible-server update `
  --resource-group crown-rg `
  --name crown-pg-dev `
  --admin-password "$newDbPassword"

# Expected: state: Ready
```

---

## 3. Update Azure App Service

```powershell
# Encode the password before placing it in a URI.
$encodedDbPassword = [System.Uri]::EscapeDataString($newDbPassword)
$newDatabaseUrl = "postgresql://crownpgadmin:$encodedDbPassword@crown-pg-dev.postgres.database.azure.com:5432/crown2026_dev?sslmode=require"

az webapp config appsettings set `
  --name crown-api-dev `
  --resource-group crown-rg `
  --settings DATABASE_URL="$newDatabaseUrl"

# Update OPS secrets
az webapp config appsettings set `
  --name crown-api-dev `
  --resource-group crown-rg `
  --settings `
    DEV_OPS_SECRET="$newOpsSecret" `
    CROWN_OPS_SECRET="$newOpsSecret" `
    CI_SMOKE_PASSWORD="$newCiPassword"

# Restart app to pick up new connection pool
az webapp restart --name crown-api-dev --resource-group crown-rg
```

---

## 4. Update GitHub Actions Secrets

```powershell
# Update OPS secret used by workflows
gh secret set DEV_OPS_SECRET `
  --body "$newOpsSecret" `
  -R tcmegahan/Crown2026

# Verify names only; secret values are not returned.
gh secret list -R tcmegahan/Crown2026
```

---

## 5. Update Local Environment

```powershell
# Edit local.secrets.ps1 (gitignored file)
notepad local.secrets.ps1

# Recompute the URI-safe value so this section is safe to run in a fresh shell.
$encodedDbPassword = [System.Uri]::EscapeDataString($newDbPassword)
$newDatabaseUrl = "postgresql://crownpgadmin:$encodedDbPassword@crown-pg-dev.postgres.database.azure.com:5432/crown2026_dev?sslmode=require"

# Update these lines.
$env:PGPASSWORD = "$newDbPassword"
$env:DEV_OPS_SECRET = "$newOpsSecret"
$env:CROWN_OPS_SECRET = "$newOpsSecret"
$env:CI_SMOKE_PASSWORD = "$newCiPassword"
$env:DATABASE_URL = "$newDatabaseUrl"

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
  -Headers @{ "X-Admin-Ops-Secret"="$newOpsSecret"; "X-School-Id"="<TENANT_ID>" } `
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
  -Headers @{ "X-Admin-Ops-Secret"="<OLD_OPS_SECRET>"; "X-School-Id"="<TENANT_ID>" }

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
