# CROWN Financial Controls Gate — 2026-05-29

## Decision

**FINANCIAL CONTROLS: NOT GREEN.**

Billing, payments, tuition, invoices, credits, refunds, financial aid, and exports require stricter certification than ordinary SIS screens. A finance feature is not complete until financial integrity, privacy, auditability, and reconciliation are proven.

## Required controls

| Control | Requirement | Status |
|---|---|---|
| FC-001 | Invoice creation is tenant-scoped and permission-controlled | NOT_GREEN |
| FC-002 | Posted invoices cannot be silently mutated | NOT_GREEN |
| FC-003 | Adjustments/credits require reason, actor, timestamp, and audit trail | NOT_GREEN |
| FC-004 | Payments reconcile to invoice/family ledger | NOT_GREEN |
| FC-005 | Duplicate payment detection exists | NOT_GREEN |
| FC-006 | Refunds are permission-controlled and audited | NOT_GREEN |
| FC-007 | Financial aid awards are privacy-restricted | NOT_GREEN |
| FC-008 | Financial aid changes are audited | NOT_GREEN |
| FC-009 | Family statements reconcile to ledger | NOT_GREEN |
| FC-010 | Export/download of financial data is permission-controlled and logged | NOT_GREEN |
| FC-011 | Support users cannot view/export finance data without approved access | NOT_GREEN |
| FC-012 | Payment provider sandbox/live separation is explicit | NOT_GREEN |
| FC-013 | Webhook signature validation is proven where payment webhooks exist | NOT_GREEN |
| FC-014 | Year-end/term rollover preserves ledger integrity | NOT_GREEN |
| FC-015 | Financial dashboard data uses live tenant-filtered sources | NOT_GREEN |

## Required evidence

```text
.crown-audit/financial-controls/latest/00_SUMMARY.md
.crown-audit/financial-controls/latest/10_control_results.csv
.crown-audit/financial-controls/latest/20_financial_permission_failures.csv
.crown-audit/financial-controls/latest/30_ledger_reconciliation.md
.crown-audit/financial-controls/latest/99_STATUS.json
```

## Status

Gate definition: **DOCUMENTED**

Certification: **NOT GREEN until financial-control tests and reconciliation artifacts pass.**
