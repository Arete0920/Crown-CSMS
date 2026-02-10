# DEV Gradebook Proof (Final)

## Purpose
Deterministic verification that DEV is seeded and gradebook endpoints return non-empty data.

## Preconditions
- Azure CLI authenticated: `az login`
- Access to resource group/app: `crown-rg / crown-api-dev`
- GitHub auth not required to run proof

## What it checks
1. `/health/` reachable and returns `ok: true`
2. Reads `CROWN_DEMO_PASSWORD` from App Service config (value never printed)
3. Auth token acquisition with admin user (token never printed)
4. Sections count > 0
5. Summary shows assignments > 0

## Run
```powershell
.\proof_dev_gradebook_final.ps1
```

## Expected output
Shows step progress + final counts:
```
[1/4] Health... OK
[2/4] Azure config... OK
[3/4] Auth... OK
[4/4] Gradebook... OK

PASS

Results:
  Health:      OK (build 5f35ab84)
  Auth:        OK
  Sections:    2
  Assignments: 12
  Students:    25
```

Exits 0 on success, 1 on failure.

## Security
- **No secrets printed**: Password read from Azure but never echoed
- **No tokens printed**: JWT acquired but never displayed
- Safe for CI/CD logs and terminal history

## After ops reset
Run this proof to verify:
1. Ops reset workflow completed successfully
2. DEV deploy finished
3. Gradebook data populated (600 entries expected: 12 assignments × 2 sections × 25 students)

## Troubleshooting

### "CROWN_DEMO_PASSWORD not found"
**Cause**: App Service config missing the setting.
**Fix**: Set in Azure Portal → App Service → Configuration, or via CLI:
```powershell
az webapp config appsettings set `
  --resource-group crown-rg `
  --name crown-api-dev `
  --settings "CROWN_DEMO_PASSWORD=<your-password>"
```

### "Azure CLI not authenticated"
**Fix**: Run `az login` and select correct subscription.

### "Auth FAIL: 401"
**Cause**: Password in Azure doesn't match what bootstrap used, OR admin user not created.
**Fix**: Re-run ops reset workflow to recreate admin user with current Azure password.

### "Zero sections" or "Zero assignments"
**Cause**: Ops reset didn't seed properly, OR wrong school_id.
**Fix**: Check ops reset workflow logs; verify `school_id=a5351136-98fe-4d48-add0-fa8f62d9ceff` used.
