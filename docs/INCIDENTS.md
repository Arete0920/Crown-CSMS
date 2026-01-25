# Incidents

When something breaks, capture what happened and how it was resolved.

Template:

## YYYY-MM-DD — <short title>
- Impact:
- Detection:
- Timeline:
- Root cause:
- Fix:
- Prevention:
- Links:

---

## 2026-01-24 — CI/CD deploy failures (resolved)
- Impact: Production deploy workflow intermittently failed until fixes landed.
- Root cause: Combination of Python/Django mismatch (historical), malformed AZURE_CREDENTIALS JSON, and workflow step issues.
- Fix: Stabilized Docker runtime (Python 3.12 for Django 6.0), corrected secret formatting, and fixed workflow steps; verified production health endpoints.
- Anchor: `prod-green-20260124-2022`
