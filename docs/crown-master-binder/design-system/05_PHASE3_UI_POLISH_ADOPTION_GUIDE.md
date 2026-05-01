# CROWN Phase 3 UI Polish Adoption Guide

Generated: 2026-04-30T03:09:55

## Installed Files

- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\styles\crown-theme.css
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\CrownDashboardFrame.tsx
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\CrownPageHeader.tsx
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\CrownKpiCard.tsx
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\CrownEmptyState.tsx
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\CrownStatusPill.tsx
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\components\crown\index.ts
- C:\w\crown_main_postmerge_verify\frontend\dashboards\src\lib\crown\ui.ts

## Global CSS Import Status

C:\w\crown_main_postmerge_verify\frontend\dashboards\src\index.css already imported

## Required Usage Pattern

```tsx
import { CrownDashboardFrame, CrownKpiCard, CrownEmptyState } from "@/components/crown";

export function AdminDashboard() {
  return (
    <CrownDashboardFrame
      eyebrow="CROWN"
      title="School Administrator Dashboard"
      subtitle="Operational view for enrollment, student records, billing, communications, and school health."
    >
      <section className="crown-grid crown-grid-4">
        <CrownKpiCard label="Enrollment" value="428" context="Seeded sandbox data" status="review" />
        <CrownKpiCard label="Attendance" value="96%" context="Today" status="pass" />
        <CrownKpiCard label="Billing" value="" context="No overdue sandbox balances" status="pass" />
        <CrownKpiCard label="Open Tasks" value="12" context="Admissions and records" status="review" />
      </section>
    </CrownDashboardFrame>
  );
}
```

## Production UI Rules

- Do not use navy-heavy or black dashboard backgrounds.
- Do not leave placeholder or fake metrics unmarked.
- Do not use dead links such as href="#".
- Do not create a new visual system per module.
- Use CROWN light royal colors, soft cards, clean spacing, and shared status pills.
- Empty states must explain next action.
- Error states must be actionable and never expose raw stack/debug text.
- Role dashboards must feel purpose-built.

## Remaining Review Counts After Phase 3

- Placeholder hits: 156
- UI risk hits: 0
- Route references: 301
- Dashboard references: 2005
- Wizard references: 842

## Evidence Files

- audit-artifacts\nonazure-phase3-ui-polish\20260430_030951\06_placeholder_hits_after.csv
- audit-artifacts\nonazure-phase3-ui-polish\20260430_030951\07_ui_risk_hits_after.csv
- audit-artifacts\nonazure-phase3-ui-polish\20260430_030951\08_route_hits_after.csv
- audit-artifacts\nonazure-phase3-ui-polish\20260430_030951\09_dashboard_hits_after.csv
- audit-artifacts\nonazure-phase3-ui-polish\20260430_030951\10_wizard_hits_after.csv
