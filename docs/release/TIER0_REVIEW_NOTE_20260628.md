# CROWN Tier 0 Review Note

Date: 2026-06-28
Repository: `tcmegahan/Crown2026`

## Current posture

Current release posture remains: **SANDBOX RELEASE CANDIDATE / PRODUCTION NOT APPROVED**.

## Owner direction

Owner direction was given to continue the controlled Tier 0 internal review preparation lane.

## Current evidence basis

- PR #1173: dashboard SWA environment flag handling and release-status wording cleanup.
- PR #1176: dashboard deploy YAML BOM hygiene cleanup.
- PR #1184: CI dashboards-build-gate rolldown native binding blocker fix.
- PR #1185: flagship sandbox reset protected-aid cleanup fix and regression coverage.
- PR #1187: release-status refresh after the June 24-28 fixes.

## Required before Tier 0 users start

1. Confirm current `main` includes #1173, #1176, #1184, #1185, and #1187.
2. Confirm no open release-blocking PRs exist.
3. Confirm current-main dashboard build gate is green after #1184.
4. Confirm `python manage.py sandbox_seed_flagship --reset` passes after #1185.
5. Confirm live sandbox endpoint proof passes after latest main deployment.
6. Confirm login, role selection, school selector, and flagship demo reset paths remain stable.

## Boundary

This note does not change the production status. Production remains **NOT APPROVED**.
