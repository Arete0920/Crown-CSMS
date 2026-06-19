# Dashboard Data Contract: compliance-audit

Dashboard key: compliance-audit
Module key: compliance-audit
Batch: 0
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS

## Purpose

Provide a compliance dashboard summary payload for compliance monitoring with metrics, alerts, and queue actions.

## Primary users

| Role | Job-to-be-done |
| ---- | -------------- |
| TBD | TBD |

## KPIs

| key | label | definition | source | filter scope | role visibility | freshness | drilldown |
| --- | ----- | ---------- | ------ | ------------ | --------------- | --------- | --------- |

## Alerts

| key | severity | condition | message | action_url | role visibility |
| --- | -------- | --------- | ------- | ---------- | --------------- |

## Queue / table

| field | label | source | role visibility | redaction rule |
| ----- | ----- | ------ | --------------- | -------------- |

## Drilldowns

| label | url | type | role visibility | permission required |
| ----- | --- | ---- | --------------- | ------------------- |

## Summary API

/api/v1/dashboards/compliance-audit/summary

## Payload contract

~~~json
{
  "dashboard_key": "compliance-audit",
  "metrics": [],
  "alerts": [],
  "queue": [],
  "meta": {}
}
~~~

## Security

- Auth required: yes
- Roles allowed: authenticated user (current proof slice)
- Roles denied: unauthenticated denied (401 proven for keyed Batch 0 summary endpoint)
- Entitlement required: no dashboard-specific entitlement gate proven in this slice
- Tenant enforcement: required and proven on the keyed compliance-audit endpoint
- Cross-tenant denial behavior: proven on the keyed compliance-audit endpoint
- Sensitive fields: no sensitive-field redaction proof captured for keyed endpoint yet
- Redaction rules: not yet proven
- Small-cell suppression: TBD
- Export rules: TBD

## Truth source

- Current backend truth source: `backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload`
- Current endpoint disclosure: sample payload metadata includes `served_from=sample`, `certification_candidate=hybrid`, and `truth_source=backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload`
- Current browser fallback disclosure: `Frontend fallback dashboard data (/api/v1/dashboards/compliance-audit/summary)`
- Certified live compliance truth source: NOT VERIFIED

## Evidence snapshot

- Backend sample truth-source proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_compliance_audit_summary_serves_sample_payload_for_request_school` (PASS)
- Unauthenticated denial proof on keyed Batch 0 summary endpoints: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_require_authentication` (PASS)
- Missing-tenant denial proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_compliance_audit_summary_requires_explicit_tenant_header` (PASS)
- Invalid-tenant denial proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_compliance_audit_summary_rejects_invalid_tenant_header` (PASS)
- Nonexistent-school denial proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_compliance_audit_summary_rejects_nonexistent_school` (PASS)
- Cross-tenant denial proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_compliance_audit_summary_blocks_cross_tenant_access` (PASS)
- Browser runtime/title/metrics proof: `docs/dashboard-completion/browser-proof/compliance-audit-20260619.md` (PASS)
- Independent review: pending

## UI states

- Loading: required
- Empty: required
- Error: required
- Forbidden: required
- Stale data: required if snapshot-backed
- Sample/fallback data: must be disclosed

## Acceptance criteria

- [ ] Contract approved
- [x] Summary service implemented
- [x] API route implemented
- [x] UI wired
- [x] Permission proof complete
- [x] Tenant proof complete
- [x] Runtime proof complete
- [ ] Independent review complete
