# Workflow Correction Plan - CI/CD & Infrastructure Fixes

## Executive Summary

Corrective action plan for 8 identified issues during 48-hour readiness strike audit. All issues addressed through implementation of CREDIBLE design patterns and bearer-token tenant isolation.

## Issues & Corrections

### Issue 1: Dashboard Honesty (CRITICAL)

**Problem**: Dashboards showed no data source indicators  
**Solution**: Implement DataStatusBanner showing 🟢 live, 🟡 fallback, ⚫ none  
**Status**: ✅ IMPLEMENTED  
**Impact**: Users now see honest readiness state

### Issue 2: Tenant Isolation (CRITICAL SECURITY)

**Problem**: X-School-Id header not injected on login  
**Solution**: Load schools_manifest.json, inject header, store in localStorage, axios interceptor  
**Status**: ✅ IMPLEMENTED  
**Impact**: Fail-closed 404 on cross-school access verified

### Issue 3: Health Endpoint (BLOCKING)

**Problem**: Only checked if database exists  
**Solution**: Return 3 states - 🔴 down (503), 🟡 seeding (202), 🟢 ready (200)  
**Status**: ✅ IMPLEMENTED  
**Impact**: Frontend can show accurate "Initializing..." vs "Ready"

### Issue 4: Seed Data (BLOCKING)

**Problem**: Missing module-specific demo data  
**Solution**: Expand seed script with module specs (attendance, grades, etc.)  
**Status**: ✅ IMPLEMENTED  
**Impact**: Dashboards render with fallback data

### Issue 5: Dashboard Wiring (CRITICAL)

**Problem**: No certification registry entries  
**Solution**: Add registry entries for sandbox-specific dashboards  
**Status**: ✅ IMPLEMENTED  
**Impact**: Dashboard certification lookups work

### Issue 6: Component State (BLOCKING)

**Problem**: No PageState/WidgetState for loading/error/empty  
**Solution**: Implement standard patterns for all states  
**Status**: ✅ IMPLEMENTED  
**Impact**: All dashboards handle edge cases

### Issue 7: Smoke Test Clarity (PROCESS)

**Problem**: No distinction between "pass rate" vs "certification ready"  
**Solution**: Separate metrics tracking  
**Status**: ✅ IMPLEMENTED  
**Impact**: Clear status visibility

### Issue 8: Visual Honesty (UX)

**Problem**: No color coding for data sources  
**Solution**: Green/orange/gray source indicators  
**Status**: ✅ IMPLEMENTED  
**Impact**: Visual clarity of data readiness

## Implementation Timeline

- ✅ Design corrections: Completed 2026-04-23
- ✅ Infrastructure validation: Completed 2026-04-23
- ✅ Runtime testing: Completed 2026-04-23
- ✅ File consolidation: In progress (automation script ready)

## Next Steps

1. Execute file consolidation via automation script
2. Commit audit artifacts to git
3. Operations proceeds with smoke testing
4. Deploy to production per readiness checklist

## Sign-Off

All 8 issues resolved. Infrastructure ready. Zero blockers identified.

---

**Prepared**: 2026-04-25  
**Status**: Ready for implementation

## 2026-05-26 Executive Delta (Current Authority)

This section supersedes the earlier "zero blockers" conclusion for dashboard release credibility.

### Current Executive Judgment

- Directionally strong architecture: shared persona template, faith/community strip, role-specific module model.
- Primary blocker remains: production-facing truth-state credibility is inconsistent.
- Root issue: widespread template fallback messaging and no universal communications strip.

### Live Evidence Snapshot

- Shared template still renders generic note banner from per-dashboard config: `launch-sandbox-banner` in `CrownDashboardTemplate`.
- Many dashboard templates still use `BASE_NOTE` from `_baseData.js`.
- Data truth pills exist on metric cards and module cards (`Live/Fallback/Loading/Unavailable`) but are not reinforced with page-level sync disclosure.
- Parent route hardening and parent note correction were implemented in current cycle.

### Release Blockers (Must Close Before Production-Grade Claim)

1. Replace production-facing sandbox note usage on persona dashboards with truth-state component behavior.
2. Add page-level data truth footer/header per persona: state + source + last synced.
3. Add universal communications strip to the shared template (same enforcement level as faith/community strip).
4. Ensure planned/inactive workflows are visually differentiated from active workflows.
5. Enforce route-guard contracts for all sensitive parent/teacher/student detail routes.

### Blocker-First Implementation Order

1. Template truth hardening
- Add shared data-truth component at template level.
- Require explicit `dataState`, `sourceLabel`, and `lastSyncLabel` defaults per dashboard.

2. Sandbox-note containment
- Restrict generic preview note wording to launch-preview-only contexts.
- Migrate persona dashboards to production-safe notes or no note when live-backed.

3. Universal communications spine
- Add `CrownCommunicationsStrip` to shared template.
- Feed each persona with unread/action-required/urgent counts.

4. Workflow truth UX
- Add `Planned/Not Active` badge style and disabled action behavior for non-live flows.

5. Contract and proof
- Expand release-hardening contracts for parent/teacher/admin route and truth-state requirements.
- Capture focused vitest proof packet for all newly enforced contracts.

### Acceptance Gates

- Gate A: No production persona dashboard displays generic sandbox copy.
- Gate B: Every persona page shows page-level data truth and last-sync disclosure.
- Gate C: Every persona page includes both faith/community and communications strips.
- Gate D: Planned workflows cannot appear visually equivalent to active workflows.
- Gate E: Route-guard contract tests pass for all sensitive role routes.

### Status

- Repository-level dashboard posture: CONDITIONAL NO-GO until Gates A-E are evidenced.
