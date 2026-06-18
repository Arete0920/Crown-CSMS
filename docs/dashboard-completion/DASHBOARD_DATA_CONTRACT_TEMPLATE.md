# Dashboard Data Contract Template

Dashboard key:
Module key:
Dashboard title:
Batch:
Owner:
Independent reviewer:

## Purpose
Describe the operational decision this dashboard supports.

## Primary users
- Role:
- Job-to-be-done:

## KPIs
| key | label | definition | source | filter scope | role visibility | freshness | drilldown |
|-----|-------|------------|--------|-------------|----------------|-----------|-----------|

## Alerts
| key | severity | condition | message | action_url | role visibility |
|-----|----------|-----------|---------|------------|----------------|

## Queue / table
| field | label | source | role visibility | redaction rule |
|-------|-------|--------|----------------|----------------|

## Drilldowns
| label | url | type | role visibility | permission required |
|-------|-----|------|----------------|---------------------|

## Summary API
```
/api/v1/dashboards/<dashboard_key>/summary/
```

## Payload contract
```json
{
  "dashboard_key": "",
  "module_key": "",
  "schema_version": "1.0",
  "served_from": "live",
  "source_module": "",
  "generated_at": "",
  "expires_at": null,
  "sensitivity_level": "internal",
  "metrics": [],
  "alerts": [],
  "queue": [],
  "drilldowns": [],
  "redactions": []
}
```

## Security
- Auth required:
- Roles allowed:
- Roles denied:
- Entitlement required:
- Tenant enforcement:
- Cross-tenant denial behavior:
- Sensitive fields:
- Redaction rules:
- Small-cell suppression:
- Export rules:

## UI states
- Loading:
- Empty:
- Error:
- Forbidden:
- Stale data:
- Sample/fallback data:

## Acceptance criteria
- [ ] Contract approved
- [ ] Summary service implemented
- [ ] API route implemented
- [ ] UI wired
- [ ] Permission proof complete
- [ ] Tenant proof complete
- [ ] Runtime proof complete
- [ ] Independent review complete
