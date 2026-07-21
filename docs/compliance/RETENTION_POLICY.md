# CROWN Data Retention Control Policy

**Status:** Technical control baseline implemented. Retention periods and legal sufficiency remain subject to business-owner and counsel approval before pilot or general availability.

This document is the single authoritative repository policy for retention controls. It defines technical safeguards; it is not legal advice and does not authorize production deletion by itself.

## Retention schedule baseline

| Data type | Technical baseline |
|---|---|
| Admissions inquiries | 365 days |
| Student records | Active enrollment plus the approved records schedule |
| Billing records | Approved legal and financial retention period |
| Prayer requests | Active plus 180 days |
| Audit logs | 7 years |
| Temporary uploads | 30 days |

The values above are repository defaults only. A production schedule requires documented approval for each data class and jurisdiction. A configured retention window must be a positive whole number of days; zero, negative, boolean, or otherwise invalid values fail closed without evaluating target records.

## Execution controls

- Every service, command, and scheduled-task invocation is non-destructive by default: target records are not deleted.
- Dry-run evaluations intentionally write durable audit evidence, so preview mode is not literally database-write-free.
- Destructive execution requires the exact confirmation phrase, an identified approver, and an explicit execution flag.
- Tenant-owned models always require a non-empty tenant or school identifier.
- Global execution applies only to models without a recognized tenant field and whose exact model label is positively listed in `CROWN_RETENTION_GLOBAL_MODEL_ALLOWLIST`.
- `--allow-global` cannot bypass tenant scope and does not itself approve any model.
- Models without a recognized tenant field fail closed when tenant execution is requested.
- Legal hold always prevents deletion, and persisted policy rows are locked and revalidated immediately before destructive work.
- Primary records are selected and deleted in bounded batches of no more than 1,000.
- The original tenant and cutoff filters are reapplied to each delete query.
- Cascading deletion is prohibited in the generic retention service. A model that would delete related rows must use a separately reviewed model-specific purge lifecycle.
- Successful deletion and its audit record are committed in the same database transaction. Audit-persistence failure rolls back the deletion.
- A deletion or policy-validation failure is recorded after rollback and propagated as a failed execution; it is not reported as success.
- Every policy evaluation writes a consistently shaped purge-audit snapshot containing mode, scope, cutoff, approver, matched count, selected count, primary-deletion count, cascade count, batch count, and rollback disposition.

## Deletion lifecycle

Where a model provides a staged deletion or archival lifecycle, that lifecycle should be completed before permanent removal. The generic retention service performs only the final, explicitly authorized, bounded, non-cascading purge after the retention window.

## Approved command patterns

Preview one tenant without deleting target records:

```text
python manage.py purge_expired_records --tenant-id <tenant-id>
```

Execute one tenant after approval:

```text
python manage.py purge_expired_records --execute --confirm PURGE_EXPIRED_RECORDS --approved-by <identity> --tenant-id <tenant-id> --batch-size 500
```

Global execution remains blocked unless all of the following are true:

1. `--allow-global` is explicitly supplied;
2. the model has no recognized tenant field;
3. the exact model label is present in `CROWN_RETENTION_GLOBAL_MODEL_ALLOWLIST`;
4. the confirmation phrase and approver identity are supplied;
5. all other legal-hold, retention-window, non-cascade, transaction, and audit controls pass.

## Release boundary

Passing repository tests demonstrates the presence of technical controls only. It does not prove configured policy rows, the production allowlist, operational scheduling, legal approval, production execution, or pilot/GA authorization.
