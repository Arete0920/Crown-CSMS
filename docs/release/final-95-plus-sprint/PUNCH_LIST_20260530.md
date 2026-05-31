# CROWN Final 95+ Sprint Punch List - 2026-05-30

Status: ACTIVE FINAL-SPRINT PUNCH LIST
Authority: Non-shipping execution control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Current sprint posture

Ready to sprint: YES.
Ready for unrestricted production release: NO.

The sprint is governed by proof, not confidence. Every item below must be closed with evidence before any production-ready claim.

## P0 - Release authority and proof blockers

### P0-1 - Refresh candidate truth

Status: NOT DONE

Required actions:

1. Pull latest `main` locally.
2. Capture exact SHA.
3. Run `docs/release/final-95-plus-sprint/VSCODE_COMMAND_PACK_20260530.md`.
4. Commit generated evidence.
5. Only then update release authority and scorecard.

Exit evidence:

- Repo truth freeze artifact.
- Backend/frontend proof artifacts.
- Evidence manifest.

### P0-2 - Close deploy SHA parity

Status: NOT DONE

Required actions:

1. Run deploy parity script against current candidate and active deploy target.
2. Capture health/integrity JSON or live URL proof.
3. Commit parity JSON/MD artifacts.
4. Update release authority only if parity passes.

Exit evidence:

- Final deploy parity packet.
- Exact candidate SHA and deploy SHA match or documented NO-GO.

### P0-3 - Publish current protected-spine packet

Status: NOT DONE

Required actions:

1. Run current protected-spine suite on exact candidate SHA.
2. Include tenant/RBAC/auth/security/object-permission/audit/idempotency proof.
3. Commit full packet.
4. Update scorecard only after pass.

Exit evidence:

- Protected-spine packet with PASS.
- Raw stdout/stderr proof.

### P0-4 - Reconcile release authority and scorecard

Status: NOT DONE

Required actions:

1. Replace stale scorecard reference or create new final scorecard.
2. Update `docs/CURRENT_RELEASE_STATUS.md` only after proof is current.
3. Keep old docs historical only.
4. No unrestricted production language until every critical gate passes.

Exit evidence:

- Current release authority.
- Current 95+ scorecard.
- No contradictory live authority claims.

## P1 - Route, API, role, and data wiring blockers

### P1-1 - Frontend route guard audit

Status: NOT DONE

Observed risk:

- Dashboard registry routes are generated through `RoleRouteGuard` and `ReleaseStateRoute`.
- Manual `router.jsx` routes still exist outside generated dashboard route handling.
- Every manual route must be classified as public, sandbox-only, launch-preview, guarded, or defect.

Required actions:

1. Generate full route inventory from `frontend/dashboards/src/routes/router.jsx`.
2. Classify each route.
3. Add tests for unguarded sensitive routes.
4. Fix any unguarded production-sensitive page.

Exit evidence:

- Final route guard audit.
- Route tests passing.

### P1-2 - API canonicalization audit

Status: NOT DONE

Observed risk:

- `backend/crown_api/api_v1_urls.py` includes specific module URLs and then a legacy `crown_api.api_urls` catch-all.
- Some frontend API calls still use `/api/...` while others use `/api/v1/...`.

Required actions:

1. Generate full API URL inventory.
2. Mark each route canonical, compatibility, deprecated, or defect.
3. Add contract tests for frontend API clients.
4. Move production claims to `/api/v1` only unless explicitly documented.

Exit evidence:

- Final API contract audit.
- API contract parity pass.

### P1-3 - Role vocabulary convergence

Status: NOT DONE

Observed risk:

- Backend role choices and frontend dashboard role groups use different vocabularies.
- This may be normalized elsewhere, but production requires explicit proof.

Required actions:

1. Generate backend role inventory.
2. Generate frontend role group inventory.
3. Generate nav permission inventory.
4. Generate role-to-route matrix.
5. Add/repair tests for every production role.

Exit evidence:

- Final role permission matrix.
- Route/nav permission tests passing.

### P1-4 - Dashboard live-data provenance expansion

Status: NOT DONE

Observed risk:

- PR #883 added operational KPI catalog and dashboard operating model.
- Current catalog covers only a subset of dashboards.
- Every production dashboard needs data provenance and honest data state.

Required actions:

1. For every dashboard registry row, identify KPI source.
2. Mark `live`, `fallback`, `sample`, `stale`, `unavailable`, or `not wired`.
3. Remove production exposure for unproven dashboards or keep behind release-state route.
4. Add tests verifying source labels and degraded-state messaging.

Exit evidence:

- Final dashboard KPI provenance matrix.
- Dashboard tests passing.

## P2 - Module completion blockers

### P2-1 - Admissions to enrollment to billing golden path

Status: NOT DONE

Required golden path:

1. Prospective family starts admissions.
2. Application is submitted.
3. Checklist is created.
4. Fee/waiver state is created.
5. Staff review/decision occurs.
6. Accepted family moves into enrollment state.
7. Contract/deposit state is updated.
8. Finance/billing handoff is created.
9. Parent status center reflects state.
10. Audit/event trail proves continuity.

Exit evidence:

- Golden-path backend test.
- Golden-path frontend/Playwright test or documented route proof.

### P2-2 - Teacher journey completion

Status: NOT DONE

Required workflows:

- Attendance.
- Gradebook.
- Comments/communications.
- Lesson plans.
- Scope and sequence.
- Curriculum import/edit.
- Online classroom/learning continuity.
- Assignments/student work.

Exit evidence:

- Teacher role journey proof.
- API/UI tests.

### P2-3 - Parent journey completion

Status: NOT DONE

Required workflows:

- Admissions start/apply/status.
- Student profile.
- Attendance.
- Grades/academic snapshot.
- Billing/payment/status.
- Aid preparation/status.
- Communications.
- Learning status.

Exit evidence:

- Parent role journey proof.
- API/UI tests.

### P2-4 - Operations modules completion

Status: NOT DONE

Required areas:

- HR.
- Facilities.
- Health office.
- Transportation.
- Food service.
- IT support.
- Safety/security.
- Fine arts.
- Library/media.
- Extended care.
- Summer camp.
- Spiritual life/service hours.
- Advancement/alumni.
- Board/governance.
- Platform operations.

Exit evidence:

- Module-by-module 95+ rows.
- Tests and data provenance proof.

## P3 - Hygiene and noise cleanup

### P3-1 - Settings cleanup

Status: NOT DONE

Required actions:

1. Remove contradictory comments/version references.
2. Split or rationalize production/local/CI settings.
3. Remove duplicate late override confusion.
4. Preserve security posture.

Exit evidence:

- `manage.py check --deploy` pass or documented expected warnings resolved.

### P3-2 - Legacy docs cleanup

Status: NOT DONE

Required actions:

1. Ensure every stale GO/SHIP/RELEASE_READY doc is clearly historical.
2. Ensure only current authority and current scorecard control release status.
3. Prevent stale docs from being used for future scoring.

Exit evidence:

- Authority hygiene audit.

### P3-3 - Encoding/noise cleanup

Status: NOT DONE

Required actions:

1. Fix mojibake in source comments/docs where present.
2. Remove placeholder language from production-facing docs.
3. Remove dead instructions and obsolete runbooks from active paths.

Exit evidence:

- Hygiene diff and checks.

## Immediate sequence

1. Run VS Code command pack.
2. Commit local evidence.
3. Inspect first failure if any.
4. Fix the first blocker only.
5. Re-run focused proof.
6. Repeat until all P0 is green.
7. Then move to P1 route/API/role/data audits.
8. Then close P2 module rows.
9. Then complete P3 hygiene.
10. Only then publish final authority and signoff.
