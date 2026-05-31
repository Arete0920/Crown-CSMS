# CROWN Final 95+ Sprint - GitHub Open Items Audit - 2026-05-31

Status: ACTIVE BLOCKER AUDIT
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This audit records current GitHub-visible unresolved work so the final sprint does not incorrectly treat the repository as clean, merged, or release-ready.

## Current GitHub finding

GitHub currently shows:

- one open pull request requiring completion/review before it can be treated as merged work;
- open issues that remain production/full-completion blockers;
- review comments on the open PR that must be resolved or explicitly dismissed with evidence.

## Open pull request

| PR | Title | State | Merged | Head | Base | Changed files | Current classification |
|---|---|---|---|---|---|---:|---|
| #884 | Close full-completion truth gate blockers | open | false | `hotfix/truth-gate-zero-blockers-20260530` @ `b77b56157148fb0dddf9b352113afb57a9861763` | `main` @ `9bdee51c19bf15b27d8804a1d8c57efd0a1334a7` | 56 | NOT COMPLETE / NOT MERGED |

## PR #884 claimed evidence

The PR body reports:

- truth-gate summary PASS with zero blockers;
- required_scope_count: 47;
- dashboard_template_blocker_count: 0;
- backend_sample_payload_signal_count: 0;
- frontend dashboard contracts passed locally;
- backend deterministic contracts passed locally;
- Django system check passed locally.

These are claims in the PR body until independently verified by current CI/local evidence and review resolution.

## PR #884 unresolved review concerns found by connector inspection

The PR comments include concerns that must be resolved before merge or release reliance:

1. `frontend/dashboards/src/hooks/useDashboardData.js`
   - Possible runtime throw from spreading `config.query` / `effectiveOptions.query` when undefined/null.
2. `frontend/dashboards/src/config/dashboardTemplates/index.js`
   - Duplicate `summerCampDashboard` import may cause syntax error.
   - Duplicate `summerCamp` key in `DASHBOARD_TEMPLATE_MAP` may silently override and make future diffs risky.
3. `frontend/dashboards/src/config/dashboardTemplates/teacherDashboard.js`
   - UTF-8 BOM before import.
   - Mojibake-corrupted user-facing strings.
4. `frontend/dashboards/src/config/dashboardTemplates/volunteerManagementDashboard.js`
   - UTF-8 BOM before import.
   - Mojibake-corrupted user-facing strings.
   - CamelCase `volunteerManagement` API endpoint may 404 if backend expects kebab-case.
5. `frontend/dashboards/src/config/dashboardTemplates/summerCampDashboard.js`
   - CamelCase `summerCamp` API endpoint may not match backend kebab-case registry and may return `unknown_dashboard`.
6. `backend/crown_api/dashboards/views.py`
   - Review comment indicates `DashboardSummaryView` may accept arbitrary `X-School-ID` without the stricter tenant validation used by other dashboard endpoints.

## Open issues

| Issue | Title | Labels / posture | Current classification |
|---|---|---|---|
| #863 | Full completion blocker: replace dashboard preview/template metrics with live data services | blocker, dashboard, full-completion, live-data, NO-GO | OPEN BLOCKER |
| #865 | Full completion blocker: backend/runtime proof required for later-tier modules | blocker, full-completion, NO-GO, later-tier, runtime-proof | OPEN BLOCKER |
| #858 | Little Lambs full build: dashboards, wizards, reporting, finance, and Crown integration | little-lambs, feature, roadmap, needs-proof | OPEN SCOPE / NEEDS PROOF |

## Issue evidence snapshots

### Issue #863

Issue body requires:

- replace template-only metrics with live service/API-backed data for every dashboard in the declared registry;
- explicit data provenance per dashboard widget;
- accurate data states: live, fallback, sample, unavailable, or error;
- certification failure if a ready dashboard is sample/template/fallback backed without documented sandbox exception;
- tests proving ready dashboards cannot hide preview/sample data.

Issue comment reports fresh 2026-05-30 truth-gate evidence remained failing at that time:

- 47 dashboard preview/unproven-data blockers;
- pass=false.

### Issue #865

Issue body requires module-level backend/runtime proof for later-tier modules, including:

- canonical backend app/service/API surface;
- live dashboard metric service/query layer;
- frontend integration to live APIs;
- permission tests;
- route/render tests;
- screenshot or Playwright artifacts;
- master completion registry evidence links.

Issue comment reports the 2026-05-30 truth gate showed:

- required scope rows=26;
- dashboard template/unproven blockers=47;
- backend sample-payload signals=76;
- pass=false.

### Issue #858

Issue requires Little Lambs full build proof before completion, including:

- dashboards;
- wizards;
- reporting;
- finance/billing;
- Crown integration;
- backend domains;
- tenant isolation;
- billing calculations;
- proof-backed API/frontend/reporting workflows.

## Sprint impact

These items mean the sprint is not clean and the product cannot be treated as complete or production-ready.

Current status:

- PR #884: NOT MERGED.
- Issues #863 and #865: OPEN BLOCKERS.
- Issue #858: OPEN SCOPE / NEEDS PROOF.
- Final-sprint evidence pack: still required.
- Production release: NO-GO.
- Sandbox release: NO-GO until evidence passes.

## Required next actions

1. Do not merge PR #884 until review comments are resolved or explicitly disproven with evidence.
2. Inspect PR #884 changed files and fix the first concrete blocker.
3. Run focused proof for the PR, including frontend build/contracts and Django check.
4. Re-run or verify CI after GitHub runner capacity/permissions are restored.
5. Close #863 and #865 only after live-data/runtime proof is current and attached.
6. Keep #858 open unless Little Lambs full-build proof is complete.
7. Update `docs/CURRENT_RELEASE_STATUS.md` only after PR/issue/evidence status supports the update.

## Current decision

NO-GO for treating GitHub as clean. The open PR and open issues are active sprint blockers.
