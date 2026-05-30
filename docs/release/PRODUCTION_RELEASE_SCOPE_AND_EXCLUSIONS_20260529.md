# Production Release Scope and Exclusions - 2026-05-29

## Included

- approved CROWN core release slice
- admissions protected slice
- public endpoint / CSRF governance
- auth/RBAC guarded baseline
- frontend truth disclosure for approved surfaces
- release and contract gates

## Excluded / NO-GO

- Scheduling PR #859
- SOLOMON content ingestion
- SOLOMON AI/intelligence activation
- publisher curriculum integration
- BJU Press content ingestion
- Teams/SharePoint federation
- curriculum maps ingestion
- student-facing SOLOMON search
- any unmerged draft PR
- any feature without hosted green gates
- any persona/dashboard route not explicitly verified

## Release Claim Rule

No module, persona, dashboard, workflow, or integration may be called production-ready unless it is:

- merged to main
- included in release scope
- tested locally
- green in hosted gates
- live-smoked where applicable
- truth-disclosure verified where frontend-facing
- explicitly documented as included
