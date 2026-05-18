# Provenance Taxonomy

## Trust Tiers

| Tier | Label | Description |
|---|---|---|
| P0 | Primary Authoritative | Original source of truth; official system, owner, policy, legal record, or canonical artifact |
| P1 | Delegated Authoritative | Approved derivative maintained by accountable owner |
| P2 | Verified Reference | Reliable supporting material, not controlling authority |
| P3 | Unverified Candidate | Potentially useful but not yet validated |
| P4 | Conflicted / Deprecated | Known conflict, supersession, or deprecation |
| P5 | Prohibited / Rejected | Not admissible for C1 |

## Provenance Fields

Each candidate source must record:

- source_id
- title
- source_type
- origin_owner
- acquisition_method
- acquired_by
- acquired_at
- custody_path
- version_or_date
- integrity_reference
- rights_basis
- provenance_tier
- review_status
- reviewer
- decision_date
- decision_rationale

## Conflict Rule

When sources conflict:

1. P0 overrides P1-P5
2. Newer approved canonical source overrides older canonical source only if supersession is explicit
3. Policy/legal authority overrides informal guidance
4. Conflicted sources remain quarantined until resolved
