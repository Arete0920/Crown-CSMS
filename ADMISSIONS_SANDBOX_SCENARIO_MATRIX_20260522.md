# Admissions Sandbox Scenario Matrix (Demo Schools)

Date: 2026-05-22
Owner: Admissions Follow-Ups Execution
Purpose: Provide repeatable, audit-ready admissions demo scenarios across demo schools with deterministic evidence capture.

## Scope

- Focus area: Admissions pipeline, conversion, role access, and degraded-data behavior.
- Environment: Sandbox with seeded mock data for demo schools.
- Evidence target: Screenshots, API traces, and role-based outcomes mapped to scenario IDs.

## Demo School Profiles

| School ID | Demo School Name | Archetype | Enrollment Target | Primary Lead Sources | Notes |
| --- | --- | --- | --- | --- | --- |
| DS-01 | Cedar Ridge Academy | K-8 faith-based neighborhood school | 420 | Website form, church referrals | Balanced intake and steady cycle |
| DS-02 | St. Gabriel Preparatory | 9-12 college preparatory | 680 | Open house, counselor referrals | Heavier review and interview stages |
| DS-03 | Trinity Classical School | K-12 classical model | 520 | Parent ambassadors, events | Strong conversion from accepted to enrolled |
| DS-04 | Bethlehem STEM Academy | 6-12 STEM-focused | 740 | Paid campaigns, website form | Higher inquiry volume and triage load |
| DS-05 | Emmanuel Early Learning | PK-5 early learning emphasis | 300 | Social media, parish bulletins | Seasonality spikes around spring |
| DS-06 | Providence Arts Conservatory | 6-12 arts concentration | 460 | Audition nights, events | Additional decision dependencies |
| DS-07 | Good Shepherd Online Hybrid | Hybrid K-12 | 880 | Digital ads, webinars | Large pipeline with remote onboarding |

## Scenario Matrix

| Scenario ID | School | Role | Objective | Preconditions | Steps | Expected Result | Audit Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADM-SBX-01 | DS-01 | Admissions Director | Validate live admissions dashboard hydration | Admissions summary API healthy; seeded by_stage values present | Open admissions dashboard, verify stage metrics and command modules | Dashboard displays live state and current pipeline distribution | Screenshot of dashboard widgets + network capture for summary endpoint |
| ADM-SBX-02 | DS-02 | Registrar | Validate conversion wizard end-to-end commit and verify | Accepted applicants seeded for current year; registrar has admissions.edit | Create session, configure year/status, load applicants, commit with confirm, verify | Session transitions DRAFT -> CONFIGURED -> APPLICANTS_LOADED -> COMMITTED -> VERIFIED; enrolled counts increase | API response payloads for each transition + before/after applicant status export |
| ADM-SBX-03 | DS-03 | Teacher (non-privileged) | Prove forbidden access for conversion workflow | Teacher role without admissions.edit/admin.view | Attempt create/configure/commit conversion session | All protected conversion actions return 403 Permission denied | Captured 403 responses + role assignment screenshot |
| ADM-SBX-04 | DS-04 | Admissions Coordinator | Validate degraded-mode behavior when optional feeds fail | Summary endpoint available; metrics/queue/timeline endpoints simulated unavailable | Load dashboard under injected optional-feed failures | Summary renders; degraded warning shown; dashboard remains usable | UI screenshot of degraded message + captured failed optional endpoint calls |
| ADM-SBX-05 | DS-05 | Admissions Director | Validate funnel conversion KPI consistency | Known seeded values for inquiry/submitted/accepted/enrolled | Compare dashboard conversion percentages to seeded source-of-truth dataset | KPI percentages match rounded expected values | KPI screenshot + seed-data reference sheet |
| ADM-SBX-06 | DS-06 | Registrar | Validate commit idempotency and confirm requirement | One preloaded conversion session with loaded applicants | Call commit without confirm, then with confirm twice | First call 400, subsequent commits return committed status without duplicate over-conversion | API logs with response codes and final enrolled count |
| ADM-SBX-07 | DS-07 | System Admin | Validate high-volume timeline activity fallback | Timeline seeded > 20 events; then timeline service degraded | Load dashboard twice (live then degraded) | Activities panel shows top timeline events when live, deterministic fallback strings when degraded | Dual screenshots + timestamped request logs |

## Repeatability Protocol

1. Reset school data using sandbox seed pack for DS-01 through DS-07.
2. Verify role mappings before each run (Admissions Director, Registrar, Teacher, System Admin).
3. Execute scenarios in ID order ADM-SBX-01 to ADM-SBX-07.
4. Capture evidence using standardized artifact naming:
   - SCENARIOID_schoolid_step_timestamp.png
   - SCENARIOID_schoolid_api_timestamp.json
5. Record result as PASS/FAIL with defect link if failed.

## Audit Readiness Checklist

- Every scenario has at least one UI proof and one API/response proof.
- Role-based permission outcomes include both authorized and forbidden paths.
- Conversion workflow includes state transitions, confirm guard, and idempotency evidence.
- Degraded-mode behavior is proven without full dashboard outage.
- Evidence bundle is indexed by scenario ID and school ID for independent replay.

## Exit Criteria

- All 7 scenarios pass on latest branch head.
- No unexplained variance between seeded truth data and displayed KPIs.
- Evidence bundle complete and reviewed by release authority delegate.
