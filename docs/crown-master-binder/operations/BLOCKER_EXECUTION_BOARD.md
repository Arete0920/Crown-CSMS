# Crown 2026 — Blocker Execution Board

> Authority Scope Notice (2026-05-29)
>
> This file is an operational blocker board and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

**Generated:** 2026-05-01
**Branch:** `readiness/sandbox-operator-freeze-20260427_222113`
**Production Status:** NO-GO — all P0 blockers below must close before GO

---

## How to Use This Board

Each row is an owner-ready action item. Work top-to-bottom within each lane.
Mark `[x]` when closed and re-run the verification command shown.

---

## Lane A — Azure / Secrets (BLOCKED — external dependency)

These cannot close until Azure provisioning completes. Notify DevOps.

| # | Priority | Signal | Owner | Action Required |
| --- | --- | --- | --- | --- |
| A1 | P0 | Frontend root returns HTTP 404 | DevOps | Confirm `AZURE_SWA_TOKEN` secret is set in GitHub repo → retrigger `deploy-dashboard.yml` |
| A2 | P0 | `build.json` returns HTTP 404 | DevOps | Same as A1 — frontend is not deployed |
| A3 | P0 | Backend live SHA does not match approved SHA | DevOps | Confirm `AZURE_CREDENTIALS` secret is set → retrigger `deploy-prod.yml` |
| A4 | P0 | Runtime persona proofs (TI-001..TI-010) not runnable | DevOps | Unblocked once A1 + A3 close |
| A5 | P0 | RBAC live role-matrix checks blocked | DevOps | Unblocked once A1 + A3 close |

**Verification (run after A1–A3):**

```powershell
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" `
     -File "scripts\execution\149_priority10_release_packet.ps1"
```

---

## Lane B — Backend Security (actionable now)

All 6 warnings from `python manage.py check --deploy`.
Fix in `backend/crown/settings/production.py` (or env-variable injection in Azure config).

| # | Priority | Code | Issue | Fix |
| --- | --- | --- | --- | --- |
| B1 | P0 | W009 | `SECRET_KEY` uses `django-insecure-` prefix | Generate a long random key; inject via `DJANGO_SECRET_KEY` env var in Azure App Service config |
| B2 | P0 | W018 | `DEBUG=True` in deploy check | Set `DEBUG=False` for production; guard with `os.environ.get('DJANGO_DEBUG', 'False')` |
| B3 | P1 | W008 | `SECURE_SSL_REDIRECT` not `True` | Set `SECURE_SSL_REDIRECT = True` in production settings (Azure terminates TLS) |
| B4 | P1 | W012 | `SESSION_COOKIE_SECURE` not `True` | Set `SESSION_COOKIE_SECURE = True` in production settings |
| B5 | P1 | W016 | `CSRF_COOKIE_SECURE` not `True` | Set `CSRF_COOKIE_SECURE = True` in production settings |
| B6 | P2 | W004 | `SECURE_HSTS_SECONDS` not set | Set `SECURE_HSTS_SECONDS = 31536000` after confirming HTTPS-only deployment |

**Note on B1/B2:** These are the only P0 security items. B3–B6 are safe defaults that Azure's TLS termination already handles, but must be set for the Django deploy check to be silent.

**Verification:**

```powershell
cmd /c "python backend\manage.py check --deploy 2>&1" | Select-String "security\."
# Target: zero lines returned
```

---

## Lane C — Frontend Build (monitor, not blocking GO)

| # | Priority | Signal | Owner | Action |
| --- | --- | --- | --- | --- |
| C1 | P2 | Chunk size warning: `index-*.js` > 500 KB (current ~2 MB) | Dev 4 | Add `manualChunks` to `vite.config.js` to split vendor/app — not blocking, Vite builds successfully |

**Build status:** PASSING (`npm run build` — 2229 modules, 7.27 s)

**Verification:**

```powershell
Set-Location frontend\dashboards; npm run build 2>&1 | Select-String "error|Error|failed"
# Target: zero lines returned
```

---

## Lane D — Backend API Schema Noise (low priority)

779 total issues from `manage.py check --deploy` are dominated by `drf_spectacular.W001`
(OpenAPI schema inference warnings). These do not affect runtime behaviour.

| # | Priority | Signal | Owner | Action |
| --- | --- | --- | --- | --- |
| D1 | P3 | `AADBearerAuthentication` has no `OpenApiAuthenticationExtension` | Dev 1 (auth) | Register an extension in `core/auth/authentication.py` — cosmetic schema only |
| D2 | P3 | Multiple serializer fields cannot resolve type hints | Dev 2/3 | Add `@extend_schema_field` or explicit type hints to `get_*` methods — cosmetic schema only |

**These are NOT release blockers.** Track in a separate tech-debt ticket after go-live.

---

## Lane E — Remaining Dashboard KPI Gaps (not blocking GO)

48 REVIEW-status dashboards missing `UsesKpiStrip` and `HasDataSourceMetadata`.
Full list in `docs/crown-master-binder/operations/DEV_PUNCH_LIST_20260430.md`.

| # | Priority | Signal | Owner | Action |
| --- | --- | --- | --- | --- |
| E1 | P0 | `CrownDashboardTemplate` missing KpiStrip | Dev 4 | Fix template first — cascades to all children |
| E2 | P1 | `AdminDashboard`, `BoardDashboard` missing KpiStrip | Dev 4 | After E1 |
| E3 | P2 | `AdmissionsDashboard`, `AttendanceDashboard` missing KpiStrip | Dev 3 + Dev 4 | After E1 |
| E4 | P3–P7 | Remaining 43 REVIEW dashboards | Dev team | Re-scan after E1 — most will auto-resolve |

**Re-scan command:**

```powershell
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" `
     -File "scripts\execution\148_priority07_hygiene_closure.ps1"
```

---

## GO Criteria Checklist

```text
[ ] A1  Frontend deploys to Azure SWA (HTTP 200 on root and build.json)
[ ] A2  Backend deploys to Azure App Service (live SHA matches approved SHA)
[ ] B1  SECRET_KEY is not django-insecure-*
[ ] B2  DEBUG=False in production
[ ] All 6 security warnings silenced (manage.py check --deploy returns 0 security.W lines)
[ ] Runtime persona proofs TI-001..TI-010 all PASS
```

Once all six boxes are checked, re-run `scripts/execution/149_priority10_release_packet.ps1`
to generate the final release artifact and update `CROWN_51x51_DEPLOYMENT_DECISION.md`.

---

## Quick-Reference Commands

```powershell
# Backend security check
cmd /c "python backend\manage.py check --deploy 2>&1" | Select-String "security\."

# Frontend build
Set-Location frontend\dashboards; npm run build

# Dashboard KPI re-scan
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" -File "scripts\execution\148_priority07_hygiene_closure.ps1"

# Full release packet (run after Azure is live)
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" -File "scripts\execution\149_priority10_release_packet.ps1"
```
