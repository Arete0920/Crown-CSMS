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
- Tenant enforcement: required, but keyed endpoint-specific proof is still pending
- Cross-tenant denial behavior: required, but keyed endpoint-specific proof is still pending
- Sensitive fields: no sensitive-field redaction proof captured for keyed endpoint yet
- Redaction rules: not yet proven
- Small-cell suppression: TBD
- Export rules: TBD

## Evidence snapshot

- Backend route and sample payload proof: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_serve_sample_payloads_in_development` (PASS)
- Unauthenticated denial proof on keyed Batch 0 summary endpoints: `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_require_authentication` (PASS)
- Cross-tenant baseline proof on dashboard summary contract endpoints: `backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked` (PASS)
- Tenant isolation baseline proof on dashboard APIs: `backend/crown_api/tests/test_dashboard_tenant_isolation.py` (PASS)
- Browser runtime proof: pending
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
- [ ] Permission proof complete
- [ ] Tenant proof complete
- [ ] Runtime proof complete
- [ ] Independent review complete
