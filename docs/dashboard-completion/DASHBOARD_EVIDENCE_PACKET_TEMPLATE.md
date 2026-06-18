# Dashboard Evidence Packet Template

Dashboard key:
Module key:
Owner:
Independent reviewer:
Status:
Date:
Branch:
Commit SHA:

## 1. Contract
- KPI definitions:
- Alert definitions:
- Queue/table/list definitions:
- Drilldown definitions:
- served_from rules:
- Freshness SLA:
- Sensitivity classification:
- Redaction rules:
- Export rules:

## 2. Backend proof
- Summary service path:
- API route:
- Serializer/schema:
- Permission class/path:
- Tenant enforcement path:
- Entitlement check path:
- Audit event path:
- Backend test path:
- Backend test command:
- Backend test result:

## 3. Frontend proof
- Dashboard page path:
- API client/hook path:
- KPI component path:
- Alert/status component path:
- Queue/table component path:
- Empty state proof:
- Error state proof:
- Forbidden state proof:
- Frontend test path:
- Frontend test command:
- Frontend test result:

## 4. Runtime proof
- Environment:
- URL:
- User role tested:
- Tenant tested:
- Playwright test path:
- Playwright command:
- Screenshot/trace path:
- Result:

## 5. Security proof
- Unauthenticated denied:
- Unauthorized role denied:
- Authorized role allowed:
- Direct URL tested:
- Cross-tenant blocked:
- Sensitive field redaction:
- Small-cell suppression, if applicable:
- Export permission proof, if applicable:

## 6. Payload sample
```json
{}
```

## 7. Independent review
Reviewer:
Date:
Decision: APPROVED / CHANGES_REQUESTED / REJECTED
Notes:

## 8. Certification decision
- Matrix row updated:
- Status promoted to:
- Remaining blockers:
