# Failed Browser Proof: dashboard-certification-center

Date: 2026-06-18
Dashboard key: dashboard-certification-center
Proof result: FAILED_BROWSER_PROOF
Source: user-provided developer laptop proof run
Main SHA tested: 64d2142a69174a7ace89ab7143b447bfda5ae6fb

## Summary

The browser proof lane was executed against a clean `origin/main` isolated worktree. Backend smoke passed and the targeted dashboard snapshot summary API test file passed, but the browser-rendered dashboard proof failed.

This is a valid failed proof artifact. It does not certify the dashboard.

## Baseline

- Isolated proof worktree: `C:\Users\JMega\OneDrive\Desktop\Crown2026_proof_main_20260618_174301`
- Tested SHA: `64d2142a69174a7ace89ab7143b447bfda5ae6fb`
- Django check: PASS
- Targeted backend test: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py`
- Targeted backend test result: `13 passed in 117.79s`

## Browser proof attempt

URL tested:

```text
http://127.0.0.1:3000/dashboard-certification-center
```

Expected text checks:

- `Dashboard Certification`
- `Dashboards Certified`
- `Mapped`
- `0`
- `40`

Observed result:

```text
FAILED_BROWSER_PROOF
```

Failed text checks:

- `Dashboard Certification`: false
- `Dashboards Certified`: false
- `Mapped`: false

Passed text checks:

- `0`: true
- `40`: true

## Observed browser body

The page rendered the fallback shell rather than the Certification Center dashboard body:

```text
Menu
Crown
x
Offline / Fallback
NAVIGATION
Administration
School Board
Finance
Financial Aid
Admissions
Academics
Billing
System Integrity
IT
Office / HR
Teacher
Parent
Student
Spiritual Life
Marketing
Home/Wizards
Notifications
Super Admin
User
Wizard Hub

School Administrator Dashboard setup wizards

Navigation service unavailable. Showing fallback menu.

Error: HTTP 400 Bad Request

Build: dev
```

## Observed runtime blockers

```text
400 http://127.0.0.1:3000/api/v1/nav/
400 http://127.0.0.1:3000/api/v1/wizards/
```

## Local artifact paths

Artifact folder:

```text
C:\Users\JMega\OneDrive\Desktop\Crown2026_proof_main_20260618_174301\audit-artifacts\dashboard-completion\browser-proof\batch0\dashboard-certification-center_20260618_174801
```

Screenshot path:

```text
C:\Users\JMega\OneDrive\Desktop\Crown2026_proof_main_20260618_174301\audit-artifacts\dashboard-completion\browser-proof\batch0\dashboard-certification-center_20260618_174801\dashboard-certification-center.png
```

JSON path:

```text
C:\Users\JMega\OneDrive\Desktop\Crown2026_proof_main_20260618_174301\audit-artifacts\dashboard-completion\browser-proof\batch0\dashboard-certification-center_20260618_174801\browser-proof.json
```

## Certification impact

- Browser route loaded at HTTP 200: PARTIAL.
- Certification Center content rendered: FAIL.
- Screenshot artifact exists locally: YES, but it captures fallback shell, not a passing dashboard render.
- Browser proof status: FAILED.
- Certification status: NOT CERTIFIED.

## Required next work

- Fix or seed runtime preconditions for `/api/v1/nav/` and `/api/v1/wizards/` so the dashboard route can render the actual Certification Center content.
- Re-run browser proof after runtime preconditions are satisfied.
- Capture passing screenshot and JSON proof.
- Update evidence packet only after passing browser proof exists.
- Complete independent review and matrix promotion after all proof rows pass.

## Non-claims

This failed proof does not certify the dashboard.
This failed proof does not approve sandbox, pilot, production, or release GO.
