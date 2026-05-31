# API Route Alias Audit

Date: 2026-05-30
Purpose: inventory API route aliases and deprecate non-essential aliases.

## Alias Inventory

| Canonical Route Surface | Alias Surface | Reason | Status |
| --- | --- | --- | --- |
| /api/v1/* | /api/* | Backward compatibility for existing clients | ESSENTIAL_LEGACY |
| /api/v1/dashboards/* | /api/dashboards/* | Legacy dashboard clients | NON_ESSENTIAL_ALIAS |

## Deprecation Decisions

| Alias Surface | Decision | Effective State | Sunset Target |
| --- | --- | --- | --- |
| /api/dashboards/* | DEPRECATE | No net-new consumers; retain temporary compatibility only | 2026-07-31 |

## Guardrails

- No new aliases may be introduced without release-owner signoff.
- Canonical APIs must remain under /api/v1/*.
- Deprecated aliases remain read-compatible only until sunset.

Enforcement:
- scripts/release/verify_api_route_alias_audit.ps1
