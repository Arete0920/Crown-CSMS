# VS Code Execution Packet: Dashboard Completion Program

Date: 2026-06-18
Scope: Local developer commands, file creation, verification, and branch workflow.

Use this packet in VS Code from the local repository root.

## 0. Ground rules

- Do not start dashboard product-code wiring until the control files and matrix are present.
- Do not mix dashboard completion work with unrelated dirty changes.
- Do not call dashboards complete because routes render.
- Do not add new canonical routes without approval.
- Do not duplicate dashboard concepts.
- Do not hide sample/fallback/stale/unavailable payload status.
- Do not ask TC to self-review certification.

## 1. Create the local work branch

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

git fetch origin main

git status --short

$branch = 'docs/dashboard-plan-20260618'
if ((git branch --list $branch).Trim()) {
  git checkout $branch
} else {
  git checkout -b $branch origin/main
}

git status --short
```

## 2. Create dashboard completion folder

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

New-Item -ItemType Directory -Force -Path 'docs\dashboard-completion' | Out-Null
New-Item -ItemType Directory -Force -Path 'audit-artifacts\dashboard-completion' | Out-Null
New-Item -ItemType Directory -Force -Path 'audit-artifacts\dashboard-completion\evidence-packets' | Out-Null
New-Item -ItemType Directory -Force -Path 'audit-artifacts\dashboard-completion\runtime-proof' | Out-Null
New-Item -ItemType Directory -Force -Path 'audit-artifacts\dashboard-completion\matrix' | Out-Null
```

## 3. Create certification matrix v2

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

@'
dashboard_key,module_key,batch,owner,independent_reviewer,status,route,page,summary_api,served_from_allowed,freshness_sla,sensitivity,roles_allowed,roles_denied,tenant_test,permission_test,frontend_test,playwright_proof,evidence_packet,blocker,next_action
dashboard-certification-center,dashboard-certification-center,0,TBD,TBD,MAPPED,TBD,TBD,TBD,live|snapshot,TBD,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
release-reliability,release-reliability,0,TBD,TBD,MAPPED,TBD,TBD,TBD,live|snapshot,TBD,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
compliance-audit,compliance-audit,0,TBD,TBD,MAPPED,TBD,TBD,TBD,live|snapshot,TBD,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
attendance,attendance,1,TBD,TBD,MAPPED,/attendance-dashboard,TBD,/api/v1/dashboards/attendance/summary/,live|snapshot,5m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
billing,billing,1,TBD,TBD,MAPPED,/billing-dashboard,TBD,/api/v1/dashboards/billing/summary/,live|snapshot,5m,financial,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
gradebook,gradebook,1,TBD,TBD,MAPPED,/gradebook-dashboard,TBD,/api/v1/dashboards/gradebook/summary/,live|snapshot,5m,academic,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
communications,communications,1,TBD,TBD,MAPPED,/communications-dashboard,TBD,/api/v1/dashboards/communications/summary/,live|snapshot,5m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
registrar,registrar,1,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/registrar/summary/,live|snapshot,5m,sensitive,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
school-administrator,school-administrator,1,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/school-administrator/summary/,live|snapshot,5m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
admissions,admissions,2,TBD,TBD,MAPPED,/admissions-dashboard,TBD,/api/v1/dashboards/admissions/summary/,live|snapshot,5m,sensitive,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
financial-aid,financial-aid,2,TBD,TBD,MAPPED,/financial-aid-dashboard,TBD,/api/v1/dashboards/financial-aid/summary/,live|snapshot,5m,financial,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
parent,parent,2,TBD,TBD,MAPPED,/parent,TBD,/api/v1/dashboards/parent/summary/,live|snapshot,5m,family,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
teacher,teacher,2,TBD,TBD,MAPPED,/teacher,TBD,/api/v1/dashboards/teacher/summary/,live|snapshot,5m,academic,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
student,student,2,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/student/summary/,live|snapshot,5m,student,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
activities-athletics,activities-athletics,2,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/activities-athletics/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
scheduling,scheduling,3,TBD,TBD,MAPPED,/scheduling-dashboard,TBD,/api/v1/dashboards/scheduling/summary/,live|snapshot,5m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
health-office,health-office,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/health-office/summary/,live|snapshot,5m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
transportation,transportation,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/transportation/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
food-service,food-service,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/food-service/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
facilities,facilities,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/facilities/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
safety-security,safety-security,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/safety-security/summary/,live|snapshot,5m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
hr,hr,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/hr/summary/,live|snapshot,15m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
it-support,it-support,3,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/it-support/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
chaplain-spiritual-life,chaplain-spiritual-life,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/chaplain-spiritual-life/summary/,live|snapshot,15m,sensitive,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
portrait-service,portrait-service,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/portrait-service/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
curriculum-pd,curriculum-pd,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/curriculum-pd/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
fine-arts,fine-arts,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/fine-arts/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
library-media,library-media,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/library-media/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
volunteer-management,volunteer-management,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/volunteer-management/summary/,live|snapshot,15m,sensitive,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
advancement,advancement,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/advancement/summary/,live|snapshot,15m,financial,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
advancement-operations,advancement-operations,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/advancement-operations/summary/,live|snapshot,15m,financial,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
alumni-relations,alumni-relations,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/alumni-relations/summary/,live|snapshot,15m,sensitive,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
school-board,school-board,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/school-board/summary/,live|snapshot,15m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
network-benchmarking,network-benchmarking,4,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/network-benchmarking/summary/,live|snapshot,1h,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
master-control,master-control,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/master-control/summary/,live|snapshot,5m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
implementation-success,implementation-success,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/implementation-success/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
data-migration,data-migration,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/data-migration/summary/,live|snapshot,15m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
integrations-automation,integrations-automation,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/integrations-automation/summary/,live|snapshot,15m,restricted,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
revenue-operations,revenue-operations,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/revenue-operations/summary/,live|snapshot,15m,financial,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
summer-camp,summer-camp,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/summer-camp/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
extended-care,extended-care,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/extended-care/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
athletics-director,athletics-director,5,TBD,TBD,MAPPED,TBD,TBD,/api/v1/dashboards/athletics-director/summary/,live|snapshot,15m,internal,TBD,TBD,PENDING,PENDING,PENDING,PENDING,,live-data-wiring,Write data contract
'@ | Set-Content -Encoding UTF8 'docs\dashboard-completion\DASHBOARD_CERTIFICATION_MATRIX_V2.csv'
```

## 4. Create evidence packet template

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

@'
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
'@ | Set-Content -Encoding UTF8 'docs\dashboard-completion\DASHBOARD_EVIDENCE_PACKET_TEMPLATE.md'
```

## 5. Create dashboard contract template

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

@'
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
|---|---|---|---|---|---|---|---|

## Alerts

| key | severity | condition | message | action_url | role visibility |
|---|---|---|---|---|---|

## Queue / table

| field | label | source | role visibility | redaction rule |
|---|---|---|---|---|

## Drilldowns

| label | url | type | role visibility | permission required |
|---|---|---|---|---|

## Summary API

```text
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
'@ | Set-Content -Encoding UTF8 'docs\dashboard-completion\DASHBOARD_DATA_CONTRACT_TEMPLATE.md'
```

## 6. Local baseline verification commands

```powershell
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = "audit-artifacts\dashboard-completion\runtime-proof\baseline_$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

python backend/manage.py check *> "$out\backend_manage_check.txt"
python backend/manage.py check --deploy *> "$out\backend_manage_check_deploy.txt"
python backend/manage.py showmigrations *> "$out\backend_showmigrations.txt"

Set-Location 'frontend\dashboards'
npm ci *> "..\..\$out\frontend_npm_ci.txt"
npm run lint *> "..\..\$out\frontend_lint.txt"
npm run test *> "..\..\$out\frontend_test.txt"
npm run test:contracts *> "..\..\$out\frontend_test_contracts.txt"
npm run check:shell-certification *> "..\..\$out\frontend_shell_certification.txt"
npm run verify:dashboard-completeness *> "..\..\$out\frontend_dashboard_completeness.txt"
npm run verify:full *> "..\..\$out\frontend_verify_full.txt"
npm run test:release:routes *> "..\..\$out\frontend_release_routes.txt"
npm run test:release:a11y *> "..\..\$out\frontend_release_a11y.txt"

Set-Location '..\..'
Get-ChildItem $out | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize
```

## 7. Commit local planning files

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

git status --short

git add docs/dashboard-completion audit-artifacts/dashboard-completion/matrix

git commit -m "docs: add dashboard completion project controls"

git status --short
```

## 8. First implementation branch after controls are merged

Do not run until the planning/control PR is merged or explicitly approved.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

git fetch origin main

git checkout -b feat/dashboard-batch0-control-services-20260618 origin/main
```

Batch 0 implementation targets:

```text
dashboard-certification-center
release-reliability
compliance-audit
```

Batch 1 implementation targets:

```text
attendance
billing
gradebook
communications
registrar
school-administrator
```
