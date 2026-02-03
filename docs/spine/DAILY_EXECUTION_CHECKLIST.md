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
