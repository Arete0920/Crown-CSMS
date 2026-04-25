# 48-Hour Operator Checklist

Date/time: 2026-04-25 12:38:40 -04:00

## Today

- [ ] Classify open PRs from audit-artifacts\48h-sandbox-prod-readiness\20260425_114916\open_prs.json
- [ ] Merge or defer artifact-only PRs
- [ ] Confirm 20 sandbox school list
- [ ] Confirm sandbox login URL
- [ ] Confirm prefilled credential behavior
- [ ] Confirm sandbox feedback form
- [ ] Confirm 4 production schools
- [ ] Confirm production onboarding contacts

## Tomorrow

- [ ] Run final smoke test for sandbox admin
- [ ] Run final smoke test for teacher
- [ ] Run final smoke test for parent
- [ ] Run final smoke test for admissions
- [ ] Run final smoke test for attendance
- [ ] Run final smoke test for gradebook
- [ ] Run final smoke test for finance/billing
- [ ] Run final smoke test for communications
- [ ] Freeze launch instructions
- [ ] Send sandbox launch packet
- [ ] Send production onboarding packet

## Hard Stop Criteria

Stop launch if any of these occur:

- Release packet checker fails.
- Tenant isolation fails.
- Login fails for sandbox admin.
- Dashboard fails to load.
- Production/sandbox data boundary is unclear.
- Open PR is classified required-before-launch and remains unmerged.
- Any required environment variable is unknown.
