# Investor-Preview Sandbox Runbook

> Authority Scope Notice (2026-05-29)
>
> This document is an operational runbook for investor-preview sandbox readiness and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

## Non-negotiable rule

Do not begin the investor-preview sandbox session unless the preflight has been run successfully on the exact build being shown.

## Required command

```powershell
.\scripts\release\demo-preflight.ps1 -BuildTag "demo-2026-03-15" -ApiBaseUrl "https://your-api-hostname/api"
```

## Required proof artifacts

- frontend/dashboards/dist/release-candidate.json
- frontend/dashboards/dist/demo-proof.json

## Required visual checks before the meeting

- App loads without blank screen.
- Top status strip shows expected build tag.
- System Status page loads.
- Release Readiness page loads.
- Demo Readiness page loads.
- Admissions pipeline list loads.
- Finance invoices list loads.
- Communications threads list loads.
- Forbidden route behaves correctly for restricted pages.
- Search, filters, and pagination persist on core list pages.

## Demo order

- Dashboard landing
- Admissions pipeline
- Finance invoices
- Communications threads
- Release Readiness page
- Demo Readiness page
- System Status page

## Red flags that cancel the demo

- blank screen
- missing build tag
- missing proof artifacts
- health endpoint unreachable
- empty critical demo surfaces
- restricted page opens without authorization
- navigation item leads to broken route
