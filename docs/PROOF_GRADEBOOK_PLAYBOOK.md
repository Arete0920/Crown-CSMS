# Proof Gradebook Playbook

## Quick Summary

**What**: Automated E2E proof that gradebook API (roster, grades, assignments) + UI work together with proper auth  
**When**: Runs on `workflow_dispatch` (manual trigger) or can be added to push/PR events  
**Status**: ✅ GREEN (locked at tag `proof-gradebook-green-20260211-0340`)

---

## Running the Workflow

### Manual Trigger (Web UI)
1. Go to: https://github.com/tcmegahan/Crown2026/actions/workflows/proof-gradebook.yml
2. Click **Run workflow**
3. Keep `main` selected
4. Click **Run workflow**

### Manual Trigger (CLI)
```bash
gh workflow run proof-gradebook.yml -R tcmegahan/Crown2026 --ref main
```

### Check Status
```bash
gh run list -R tcmegahan/Crown2026 --workflow proof-gradebook.yml -L 1
```

### View Logs (if failed)
```bash
gh run view <run-id> -R tcmegahan/Crown2026 --log-failed
```

---

## What "Green" Actually Means

✅ **All 10 steps completed successfully:**

1. **Checkout** — Code downloaded from `main`
2. **Guardrail (versions)** — Node, Python, Pip available
3. **Python setup** — 3.11 installed, pip upgraded
4. **Backend deps** — requirements.txt installed
5. **Django migrations** — DB schema created
6. **Seed DB** — 4-step bootstrap:
   - `golden_path_bootstrap` (admin user, financial data)
   - `seed_demo_school` (head@crown-demo.local, 25 families, staff)
   - `seed_academics_demo` (MATH-101, ENG-101 courses + sections)
   - `seed_gradebook_demo` (grades, assignments, categories)
7. **Django server** — Starts on 127.0.0.1:8000, health check passes
8. **Node setup** — 20.x installed
9. **Frontend** — Vite dev server on 127.0.0.1:3000, health check passes
10. **API proof** — Playwright test:
    - Logs in as `head@crown-demo.local` (password: `demo1234`)
    - Fetches first section from API (no hardcoded UUIDs)
    - Calls 3 endpoints: roster (200), grades (200), assignments (200)
    - All return 200 with proper auth headers
11. **UI proof** — Playwright test:
    - Logs in, navigates to Academics
    - Captures roster, gradebook, assignments screenshots
    - Verifies UI is responsive and data visible

---

## Reading Failures

### Pattern 1: Bootstrap Failed
**Log message**: `BOOTSTRAP_OK` missing or `manage.py` error

**What it means**: DB seed didn't complete

**Fix**: Check `CROWN_DEMO_PASSWORD` is set in workflow env or GitHub Secrets

---

### Pattern 2: Django Server Didn't Start
**Log message**: `API did not come up in time` or `Health check failed`

**What it means**: Django crashed or migrations incomplete

**Debug**: Check migration output, check if there are new model changes

**Fix**: Ensure all migrations are applied (`python manage.py showmigrations`)

---

### Pattern 3: API Proof Failed - 404/500
**Log message**: `Roster: 404` or `Grades: 500`

**What it means**: Section wasn't created or section ID wrong

**Why it happens**: `seed_academics_demo` didn't run or failed

**Fix**: Ensure workflow calls `seed_academics_demo --school-id <uuid>` after `seed_demo_school`

---

### Pattern 4: Auth Failed - Token Not Captured
**Log message**: `Token not found in login response, cookies, or sessionStorage`

**What it means**: Login response didn't match the Playwright matcher

**Why it happens**: 
- Password changed and auth failed
- Auth endpoint path changed (e.g., `/api/v1/auth/token/` became `/api/auth/jwt/login/`)

**Fix**: 
- Check password matches seed command (should be `demo1234`)
- Update matcher in test if auth endpoint changed:
  ```typescript
  const loginResponsePromise = page.waitForResponse((r) =>
    r.request().method() === "POST" && 
    r.url().includes("/api/") && 
    r.url().includes("token")  // ← adjust if needed
  );
  ```

---

### Pattern 5: UI Proof Timed Out
**Log message**: `Test timeout of 30000ms exceeded` or `waiting for getByTestId(...)`

**What it means**: UI element didn't render or auth failed

**Why it happens**:
- Frontend didn't load (Vite server down)
- Section wasn't found on page
- Auth token invalid

**Debug**: Check Vite logs, check if `seed_academics_demo` created sections

---

## When to Change Seeds vs Tests

### Change `seed_demo_school` Arguments If:
- You need different number of students: `--students 50`
- You need different tuition: `--tuition 15000`
- You're testing a different school scenario

**Do not change**:
- Username: `head@crown-demo.local` (test depends on it)
- Password: `demo1234` (test depends on it)

---

### Change `seed_academics_demo` If:
- You need different courses (currently MATH-101, ENG-101)
- You need different sections per course
- You need grades in different categories

**Current behavior**:
- Creates 2 courses (MATH, ENG) with 2 sections each
- Enrolls first 25 students per section
- Deterministic (same UUIDs every run)

---

### Change Playwright Test If:
- Auth response format changes (token field name, endpoint path)
- Section serializer changes (field names)
- API response structure changes (results/data wrapper)

**Key principle**: 
- Test should never hardcode UUIDs
- Test should fetch realistic data from the API after auth
- Token should come from login response, never from storage scraping

---

## Where Details Are Documented

| Topic | File |
|-------|------|
| **CI contract** | [docs/CANON_CI_CONTRACT.md](CANON_CI_CONTRACT.md) |
| **Branch protection** | [docs/BRANCH_PROTECTION_SETTINGS.md](BRANCH_PROTECTION_SETTINGS.md) |
| **Workflow definition** | [.github/workflows/proof-gradebook.yml](.github/workflows/proof-gradebook.yml) |
| **API proof test** | [frontend/dashboards/tests/api/gradebook-api-proof.spec.ts](frontend/dashboards/tests/api/gradebook-api-proof.spec.ts) |
| **UI proof test** | [frontend/dashboards/tests/ui/gradebook-ui-proof.spec.ts](frontend/dashboards/tests/ui/gradebook-ui-proof.spec.ts) |
| **Golden path bootstrap** | [backend/core/management/commands/golden_path_bootstrap.py](backend/core/management/commands/golden_path_bootstrap.py) |
| **Demo school seed** | [backend/core/management/commands/seed_demo_school.py](backend/core/management/commands/seed_demo_school.py) |
| **Academics seed** | [backend/academics/management/commands/seed_academics_demo.py](backend/academics/management/commands/seed_academics_demo.py) |
| **Gradebook seed** | [backend/gradebook/management/commands/seed_gradebook_demo.py](backend/gradebook/management/commands/seed_gradebook_demo.py) |

---

## Checkpoint Reference

**Latest Green Run**:
- Tag: `proof-gradebook-green-20260211-0340`
- Commit: `e8524285`
- Run: [#21898088776](https://github.com/tcmegahan/Crown2026/actions/runs/21898088776)

If workflow breaks, compare against this tag to understand what changed.

---

## The One Golden Rule

**Contract > Assumption**

- Don't assume sections exist (fetch from API)
- Don't assume token is in sessionStorage (capture from response)
- Don't assume auth endpoint path (check authClient.js + use strict matcher)
- Don't assume seed creates the same data (it does, but verify)

Follow the contract defined in `CANON_CI_CONTRACT.md` — that's the source of truth.
