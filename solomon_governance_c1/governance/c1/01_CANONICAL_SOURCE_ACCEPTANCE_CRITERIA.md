# Canonical Source Acceptance Criteria

A source may be accepted into Corpus C1 only if all required controls are satisfied.

## Required Criteria

| Control | Requirement | Result |
|---|---|---|
| Authority | Source origin is authoritative, primary, or explicitly delegated | REQUIRED |
| Provenance | Source lineage is known and documentable | REQUIRED |
| Custody | Acquisition path is recorded | REQUIRED |
| Integrity | Hash or equivalent fixed reference is recorded where applicable | REQUIRED |
| Rights | Usage permission or internal authorization is documented | REQUIRED |
| Scope Fit | Source belongs within approved C1 corpus scope | REQUIRED |
| Version Clarity | Version, date, or publication state is known | REQUIRED |
| Conflict Review | Known conflicts with existing sources are identified | REQUIRED |
| Privacy Review | Sensitive, regulated, or restricted data is flagged | REQUIRED |
| Revocation Path | Source can be quarantined or removed if challenged | REQUIRED |

## Disqualifying Conditions

A source must be rejected or quarantined if:

- origin is unknown
- authority cannot be established
- custody path is undocumented
- usage rights are unclear
- source contains prohibited data
- source is materially obsolete without historical labeling
- source conflicts with a higher-trust canonical source
- source integrity cannot be reasonably established

## Acceptance Outcomes

Allowed decisions:

- APPROVED_CANONICAL
- APPROVED_REFERENCE_ONLY
- QUARANTINED_PENDING_REVIEW
- REJECTED
- ESCALATED
