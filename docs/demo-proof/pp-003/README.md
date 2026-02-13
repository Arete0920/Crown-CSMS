# pp-003 Demo Proof

**Golden Tag:** `demo-feb16-gradebook-edit-pp-003`  
**SHA:** `aec71930dffba0e1d186e49468ff67f77df5ead9`  
**Status:** Locked & frozen (no further changes to tag)

## Screenshots

### academics.png
Academics (Read-only) page showing Teacher Sections list.
- All 22 sections loaded
- ENG-101 with 4 students confirmed
- Dev JWT modal with credentials pre-filled

### gradebook.png
Gradebook for ENG-101 (first section, 4 students).
- ✅ 5 assignment headers (Homework 1, Quiz 1-4)
- ✅ 4 student rows (Ava Brooks, Ben Brooks, Chloe Cruz, Dylan Cruz)
- ✅ All grade cells populated (9.33/10, 19.37/20, etc.)
- ✅ FK-backed data live (assignment_name from Assignment.name)
- ✅ No console errors
- ✅ Tenant header correct (X-School-Id in DevTools Network)

## Verified Components

- Backend: Django running on port 8000 ✅
- Frontend: React Vite running on port 3000 ✅
- Database: Connected and healthy ✅
- Authentication: JWT issued and accepted ✅
- API: All endpoints returning seeded data ✅
- UI: Deterministic rendering (data-testid selectors in place) ✅

## Known Minor Issues (Non-blocking)

- Floating point precision in grade totals (174.82999999999998 / 240)
  - **Impact:** Cosmetic only. Does not affect grade calculation or cell editing.
  - **Fix:** Round totals to 2 decimals (future task, not MVP blocker)

## Demo Walkthrough

```bash
# Boot from tag
git checkout demo-feb16-gradebook-edit-pp-003
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\RUN_PROOF_NO_MANUAL_CLEANUP.ps1 -APITimeout 30

# Click path (UI)
1. Open http://127.0.0.1:3000
2. Login: head@crown-demo.local / demo1234
3. Academics → Sections → ENG-101 → Gradebook
4. See 5 assignments, 4 rows, live grades
```

## Tag Verification (Final)

```
origin/main: aec71930dffba0e1d186e49468ff67f77df5ead9
demo_tag:   aec71930dffba0e1d186e49468ff67f77df5ead9
match: YES ✓
```

**What this means:** Tag is **frozen** at proven hardening commit (aec71930). Proof scripts and logs in `proof/` directory are audit artifacts supporting that tag. Main branch can advance with docs independently without retagging.

## Status

**This tag is locked for investor demo (Feb 16).**

- Tag will not move until after demo completion
- Main branch continues to evolve with documentation and improvements
- No code changes to tag unless critical bug found (requires new PR + retag)

## Release Process

See [PROCESS_CANON.md](./PROCESS_CANON.md) for workflow details.
