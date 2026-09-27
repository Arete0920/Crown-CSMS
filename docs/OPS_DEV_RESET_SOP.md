# DEV Reset + Proof SOP

## Purpose
Standard operating procedure for resetting DEV environment and verifying gradebook data is populated.

**Owner**: Operations / DevOps
**Last Updated**: 2026-02-10
**Canon Tag**: `proof-dev-gradebook-v1`

---

## Prerequisites

Before starting, ensure:
- Azure CLI authenticated: `az login` (with access to `crown-rg` / `crown-api-dev`)
- GitHub CLI authenticated: `gh auth status`
- PowerShell 5.1+ or PowerShell 7+
- You are in the repository root: `$PWD` = `Crown-CSMS/`

---

## Step 1: Trigger Ops Reset Workflow

This will migrate, reseed, and populate gradebook data in DEV.

```powershell
$school_id = "a5351136-98fe-4d48-add0-fa8f62d9ceff"

gh workflow run -R Arete0920/Crown-CSMS ops-reset-dev.yml \
  --ref main \
  -f school_id=$school_id
```

**What happens:**
- Runs `migrate --noinput`
- Runs `golden_path_bootstrap --force` (creates admin user)
- Seeds academics (2 courses, 2 sections, 25 students)
- Seeds gradebook (12 assignments × 2 sections × 25 students = 600 entries)
- Seeds category weights

**Expected result:**
- Workflow completes in ~5 minutes
- Check status: `gh run list -R Arete0920/Crown-CSMS --workflow ops-reset-dev.yml --limit 1 --json status,conclusion`

---

## Step 2: Trigger DEV Deploy Workflow

This will redeploy the latest main branch to crown-api-dev Azure App Service.

```powershell
gh workflow run -R Arete0920/Crown-CSMS stabilization-20260116-spine_crown-api-dev.yml --ref main
```

**What happens:**
- Pulls latest code from `main`
- Builds and pushes Docker image
- Deploys to Azure App Service

**Expected result:**
- Deploy completes in ~10 minutes
- DEV is running the latest code with fresh data

---

## Step 3: Run Proof Script

This verifies DEV is healthy and gradebook data is populated.

```powershell
.\proof_dev_gradebook_final.ps1
```

**What it checks:**
1. `/health/` endpoint reachable
2. `CROWN_DEMO_PASSWORD` exists in Azure App Service config
3. Admin user authentication works
4. Sections list returns > 0 sections
5. Gradebook summary shows > 0 assignments

**Expected output:**
```
[1/4] Health... OK
[2/4] Azure config... OK
[3/4] Auth... OK
[4/4] Gradebook... OK

PASS

Results:
  Health:      OK (build <sha>)
  Auth:        OK
  Sections:    2
  Assignments: 12
  Students:    25
```

**Exit code:** 0 = success, 1 = failure

---

## Verification Checklist

After all three steps complete:

- [ ] Ops reset workflow: `status=completed, conclusion=success`
- [ ] DEV deploy workflow: `status=completed, conclusion=success`
- [ ] Proof script: `ExitCode=0` and all 4 checks show "OK"
- [ ] Proof output shows `PASS`

If any step fails, **STOP** and check troubleshooting below.

---

## Security Notes

**Passwords & Tokens:**
- Proof script reads `CROWN_DEMO_PASSWORD` from Azure but **never prints it**
- JWT tokens are acquired but **never displayed**
- Safe to run in CI/CD logs and terminal history
- No secrets will appear in output

**Access Requirements:**
- Azure: Read access to `crown-rg` / `crown-api-dev` app settings
- GitHub: Write access to workflows (to trigger runs)

---

## Troubleshooting

### 1. Ops Reset Workflow Fails

**Symptom:** Workflow shows `status=failed` or `conclusion=failure`

**Diagnosis:**
```powershell
$runId = (gh run list -R Arete0920/Crown-CSMS --workflow ops-reset-dev.yml --limit 1 --json databaseId --jq ".[0].databaseId").Trim()
gh run view $runId -R Arete0920/Crown-CSMS --log | Select-String -Pattern "(error|ERROR|fail|FAIL)" -Context 2,2
```

**Common Causes:**
- DEV App Service temporary connectivity issue
- Migration conflict (old schema drift). **Fix:** Delete manually, re-run.
- Bootstrap user creation failed. **Fix:** Ensure `CROWN_DEMO_PASSWORD` is set in Azure.

### 2. Proof Script: "Azure config... FAIL"

**Symptom:** `[2/4] Azure config... FAIL`

**Diagnosis:**
- Check Azure CLI login: `az account show`
- Check app settings exist: `az webapp config appsettings list -g crown-rg -n crown-api-dev`

**Fix:**
```powershell
az login
# Follow browser auth, select correct subscription
./proof_dev_gradebook_final.ps1
```

### 3. Proof Script: "Auth... FAIL"

**Symptom:** `[3/4] Auth... FAIL` with `401 Unauthorized`

**Diagnosis:**
- Admin user may not exist (ops reset didn't complete)
- Password mismatch between Azure and what bootstrap used

**Fix:**
- Verify ops reset workflow completed successfully
- Re-run ops reset if needed: `gh workflow run ... ops-reset-dev.yml`
- Then re-run proof script

### 4. Proof Script: "Gradebook... FAIL"

**Symptom:** `[4/4] Gradebook... FAIL` with `Zero sections` or `Zero assignments`

**Diagnosis:**
- Seeding didn't run (ops reset issue)
- Wrong school_id used

**Fix:**
- Verify school_id: `a5351136-98fe-4d48-add0-fa8f62d9ceff` (hardcoded in proof script)
- Check ops reset logs: `gh run view <runId> -R Arete0920/Crown-CSMS --log`
- Re-run ops reset if gradebook seeding lines missing

---

## Post-Reset State

After successful completion:

- **Sections:** 2 (MATH-101-2026-SPRING, ENG-101-2026-SPRING)
- **Students per section:** 25
- **Assignments per section:** 12
- **Total GradeEntry records:** 600 (25 × 12 × 2)
- **Admin user:** `admin` (password from Azure `CROWN_DEMO_PASSWORD`)
- **Build SHA:** Latest from `main` branch

---

## Automation (Optional)

To automate this as a scheduled task (e.g., weekly reset):

```powershell
# PowerShell scheduled task
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -Command `
  'cd C:\...\Crown-CSMS; gh workflow run ... ops-reset-dev.yml; Start-Sleep 600; .\proof_dev_gradebook_final.ps1'"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 2am

Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "DEV-Reset-Weekly" -RunLevel Highest
```

Or as a GitHub Actions scheduled workflow (`.github/workflows/scheduled-dev-reset.yml`):
```yaml
on:
  schedule:
    - cron: '0 2 * * MON'  # Every Monday at 2 AM UTC

jobs:
  dev-reset:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trigger ops reset
        run: gh workflow run ops-reset-dev.yml -f school_id=a5351136-98fe-4d48-add0-fa8f62d9ceff
```

---

## FAQ

**Q: Do I need to manually delete the old data?**
A: No, ops reset includes `wipe=True` for gradebook entries, so it cleans up before reseeding.

**Q: How long does the full reset take?**
A: 15-20 minutes total (5 min reset workflow + 10 min deploy + 1 min proof).

**Q: Can I re-run the proof script multiple times?**
A: Yes, it's read-only and deterministic. No side effects.

**Q: What if I want to reset a different school?**
A: Modify the `school_id` parameter in Step 1. Current default is the demo school.

**Q: Is the proof script safe for CI/CD?**
A: Yes. No secrets printed, exit codes are deterministic, handles errors gracefully.

---

## Reference

- Config: [CROWN_DEV_CANON.md](CROWN_DEV_CANON.md)
- API Routes: [backend/crown_api/api_v1_urls.py](backend/crown_api/api_v1_urls.py)
- Proof Script: [proof_dev_gradebook_final.ps1](proof_dev_gradebook_final.ps1)
- Proof Docs: [docs/PROOF_DEV_GRADEBOOK_FINAL.md](docs/PROOF_DEV_GRADEBOOK_FINAL.md)
- Ops Reset Workflow: [.github/workflows/ops-reset-dev.yml](.github/workflows/ops-reset-dev.yml)
- Deploy Workflow: [.github/workflows/stabilization-20260116-spine_crown-api-dev.yml](.github/workflows/stabilization-20260116-spine_crown-api-dev.yml)

---

## Sign-Off

**This procedure verified operationally on:** 2026-02-10
**Next review date:** TBD (after first team execution)
