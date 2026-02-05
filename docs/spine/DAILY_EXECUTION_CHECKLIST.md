# Crown2026 — Daily Execution Checklist (Printable)
**Sprint Window:** Feb 2–Feb 16, 2026  
**Rule:** If Golden Path is not green, nothing else matters.

---

## DAILY STARTUP (15–20 minutes)
- [ ] Open repo in VS Code
- [ ] `git pull`
- [ ] Confirm branch: `main` (or `release/feb16-freeze` if still in pre-merge)
- [ ] **CANON:** Check GitHub Actions `proof-ceremony` result on `origin/main` (this is the authoritative gate)
- [ ] Check GitHub Actions page for unexpected runs (should be none scheduled)

**Stop condition:** You are oriented, and the system is in a known state.

**CI Proof Ceremony (Step 19 Canon):**
- Runs on every PR and push to release/* branches
- Verifies: Health ✅ | Auth ✅ | Migrations ✅ | Pytest 7/7 ✅
- Python: 3.13 | Driver: psycopg v3 | Seed: --wipe | Tests: backend/tests/test_director_actions.py
- Must pass before merging to main (required going forward)
- Local proof_step16.ps1 may fail; ignore if CI proof is GREEN

---

## AZURE DEV SMOKE TEST (5 minutes)
**Goal:** Prove Azure DEV is running the correct build with all spine endpoints live.  
**Note:** Use `curl.exe` (not `curl`) in PowerShell to avoid alias behavior.

**Quick setup (copy/paste these variables):**
```powershell
$BASE="https://crown-api-dev.azurewebsites.net"
$TOKEN="PASTE_VALID_JWT"  # obtain via standard login flow (see Check 3)
```

### Check 1 — Build SHA is correct
```powershell
$BASE="https://crown-api-dev.azurewebsites.net"
curl.exe -sS "$BASE/api/health/" | ConvertFrom-Json | Format-List
```
**Pass criteria:** `build_sha` matches the commit you expect (check `git log --oneline -1`).

---

### Check 2 — Unauth tenant guard works (should be 403 + message)
```powershell
curl.exe -sS -i "$BASE/api/billing/invoices/" 2>&1 | Select-Object -First 25
```
**Pass criteria:**
- `HTTP/1.1 403`
- Body contains: `school_id could not be derived`

---

### Check 3 — Authenticated invoices returns 200
```powershell
# Get a valid JWT via the standard login flow (DevJwtPanel or /api/v1/auth/login/).
# Use a user authorized for the target school/tenant.

curl.exe -sS -i -H "Authorization: Bearer $TOKEN" "$BASE/api/billing/invoices/" 2>&1 | Select-Object -First 40
```
**Pass criteria:**
- `HTTP/1.1 200`
- JSON array with at least one invoice object (or empty array `[]` is acceptable)

---

### 409 OneDeploy Lock Drill (When GitHub Actions deploy fails with CODE: 409)

**Symptom:** GitHub Actions deploy fails with `Conflict (CODE: 409)`.

**Fix (canonical):**
1. Confirm no GH runs queued/in_progress:
   ```powershell
   gh run list --workflow="stabilization-20260116-spine_crown-api-dev.yml" --limit 10
   ```
   If any runs show `in_progress` or `queued`, cancel them:
   ```powershell
   gh run cancel <RUN_ID>
   ```

2. Restart App Service:
   ```powershell
   az webapp restart -g crown-rg -n crown-api-dev
   ```

3. Re-run deploy workflow:
   ```powershell
   gh workflow run "Build and deploy Python app to Azure Web App - crown-api-dev" --ref main
   ```

4. **Escalation (if 409 persists):**
   - Portal → crown-api-dev → Advanced Tools → Go (Kudu)
   - Kudu → Process Explorer (check for stuck deployment process)
   - App Service → Deployment Center → Logs (check for locked deployments)

**Stop condition:** All 3 smoke checks pass, or documented blocker exists.

---

## WORK BLOCKS (Weekdays: 8 hours)

### BLOCK 1 — Stability First (2 hours)
Allowed:
- [ ] Golden Path failures only
- [ ] Environment variable fixes (documented)
- [ ] CI checks required for merge
- [ ] Tenant/RBAC correctness issues
Not allowed:
- [ ] New features
- [ ] New modules
- [ ] Refactors

**Stop condition:** Stability is improved, not broadened.

---

### BLOCK 2 — Core Build / Hardening (3 hours)
Only tasks tied directly to Feb 16 buyer readiness:
- [ ] Admissions reliability (demo path)
- [ ] Financial Aid reliability (demo path)
- [ ] Billing/Tuition reliability (demo path)
- [ ] Attendance reliability (demo path)
- [ ] Communications reliability (demo path, if in scope)
- [ ] Seed/migration fixes that block demo or health proof

**Stop condition:** Demo path became more reliable, not more ambitious.

---

### BLOCK 3 — Docs & Proof (1.5 hours)
- [ ] Update spine docs
- [ ] Update recovery notes
- [ ] Update buyer positioning notes (if reality changed)
- [ ] Capture exact commands used today

**Stop condition:** Tomorrow-you will not guess.

---

### BLOCK 4 — Cost & Control Check (30 minutes)
- [ ] Confirm scheduled workflows are OFF
- [ ] Cancel any stuck runs
- [ ] Avoid rerunning CI more than needed

**Stop condition:** No surprise bills.

---

### BLOCK 5 — End-of-Day Lock (1 hour)
- [ ] `git status` clean (ignore-only untracked artifacts)
- [ ] Commit only working changes
- [ ] Push once
- [ ] Confirm CI results (if triggered) are green
- [ ] Write 3-line daily note:
  - What changed
  - What’s stable now
  - What’s next

**Stop condition:** You can stop without anxiety.

---

## WEEKEND MODE (15-hour days)

### MORNING (4 hours)
- [ ] Run Golden Path repeatedly
- [ ] Force known failure scenarios (auth fail, tenant missing header)
- [ ] Confirm errors are clear and recoverable

### MIDDAY (6 hours)
- [ ] Demo rehearsal (full run)
- [ ] Tenant/RBAC edge cases
- [ ] Remove dead ends (docs or UI links only; no risky refactors)

### AFTERNOON (3 hours)
- [ ] Polish docs (spine + buyer notes)
- [ ] Update roadmap/sequence (factual)

### FINAL 2 HOURS
- [ ] Final Golden Path run
- [ ] Tag or note known-good state (if you are tagging)
- [ ] No risky changes late

---

## WHEN SOMETHING BREAKS (Decision Tree)
- [ ] Identify failure category: BOOT / AUTH / TENANT / SEED / CONTRACT
- [ ] Make ONE change
- [ ] Re-run Golden Path
- [ ] If it fails twice: stop, revert, resume next block/day

---

## DONE FOR THE DAY WHEN
- [ ] Golden Path / health proof passes
- [ ] No surprise automation running
- [ ] Notes written
- [ ] You feel less frantic than when you started
- [x] Step 14 proof complete (auth + tenant header + core endpoint)

---
**Reminder:** Progress = reduced uncertainty, not more code.
