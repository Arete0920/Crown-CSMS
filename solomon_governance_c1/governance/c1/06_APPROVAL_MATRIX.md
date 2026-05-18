# C1 Approval Matrix

| Decision | Meaning | Allowed Next State |
|---|---|---|
| APPROVED_CANONICAL | Source accepted as canonical for C1 | Eligible for future ingestion only after separate ingestion gate |
| APPROVED_REFERENCE_ONLY | Source may support review but is not canonical | Reference register only |
| QUARANTINED_PENDING_REVIEW | Source requires more evidence or conflict resolution | Quarantine register |
| REJECTED | Source is inadmissible | Rejected register |
| ESCALATED | Higher authority decision required | Escalation queue |

## Minimum Approval Authority

| Source Type | Required Reviewer |
|---|---|
| Policy / governance | Governance owner |
| Legal / contractual | Legal or delegated authority |
| Technical architecture | Technical owner |
| Operational procedure | Process owner |
| Training / knowledge material | Corpus steward |
| Sensitive data source | Privacy/security reviewer |

## Decision Integrity Rule

No source may be marked APPROVED_CANONICAL without:

- reviewer identity
- decision date
- rationale
- provenance tier
- rights basis
- custody path
