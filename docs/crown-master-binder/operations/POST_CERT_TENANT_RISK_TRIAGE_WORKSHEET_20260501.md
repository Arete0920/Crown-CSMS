# Tenant Risk Triage Worksheet - 2026-05-01

## Scope
This worksheet is for manual adjudication of tenant-risk static scan findings from:
C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_131601\24_tenant_risk_scan.csv

## Objective
Classify findings quickly with evidence-first decisions and isolate real cross-tenant bypass risk.

## Decision categories
- Confirmed Risk: real path to cross-tenant data access or unsafe authorization behavior.
- Benign Pattern: wording-only false positive or safe pattern with enforced guardrails.
- Needs Runtime Proof: unclear from code scan; requires explicit runtime test.
- Out of Scope: non-runtime text, docs, or unrelated scripts.

## Prioritization
- P0: endpoint/view/service code that can expose cross-tenant data or bypass role checks.
- P1: code with AllowAny/school_id=None that appears sensitive but may be intentionally safe.
- P2: docs/text references to bypass language without executable risk.

## Triage table
| Finding ID | File | Line | Snippet | Category | Priority | Owner | Decision | Evidence | Follow-up action |
|---|---|---|---|---|---|---|---|---|---|
| TR-001 |  |  |  |  |  |  |  |  |  |
| TR-002 |  |  |  |  |  |  |  |  |  |
| TR-003 |  |  |  |  |  |  |  |  |  |
| TR-004 |  |  |  |  |  |  |  |  |  |
| TR-005 |  |  |  |  |  |  |  |  |  |
| TR-006 |  |  |  |  |  |  |  |  |  |
| TR-007 |  |  |  |  |  |  |  |  |  |
| TR-008 |  |  |  |  |  |  |  |  |  |
| TR-009 |  |  |  |  |  |  |  |  |  |
| TR-010 |  |  |  |  |  |  |  |  |  |

## Fast triage rubric
1. Does this code execute on a production request path?
2. Is there an explicit tenant scope guard before data read/write?
3. Is there a role check at API and service layers?
4. Can school context be injected or switched without authorization?
5. Is there direct object lookup without scoped queryset?

If any answer is unsafe, classify as Confirmed Risk (P0) until disproven.

## Exit criteria
- All P0/P1 findings have a decision and evidence.
- Every Needs Runtime Proof item is mapped to a TI-* or RBAC-* runtime row.
- Final triage summary includes counts by category and unresolved risks.

## Summary block
- Total findings reviewed:
- Confirmed Risk:
- Benign Pattern:
- Needs Runtime Proof:
- Out of Scope:
- Unresolved P0:
