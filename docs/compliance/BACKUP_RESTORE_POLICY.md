# CROWN Backup and Restore Policy

**Status:** DRAFT PROCEDURE COMPLETE / CONFIGURATION AND RESTORE PROOF NOT EVIDENCED  
**Version:** 1.0  
**Prepared:** 2026-10-07  
**Accountable role:** Founder/Product Owner  
**Approval record:** Not recorded  
**Review:** At least annually and after material storage or deployment changes

## Scope and inventory

Inventory production databases, uploaded files, required application configuration, recovery dependencies, audit records, and encryption-key recovery arrangements. Include provider, environment, tenant/data categories, accountable owner, backup method, region, encryption, access, schedule, retention, restore dependencies, and deletion behavior. Source control is not a backup for customer records. Provider backup availability is not proof that CROWN can restore its complete service.

## Proposed baseline and objectives

These are proposed minimum operating requirements, not measured capabilities or customer commitments.

- Automated daily backups for in-scope customer databases and files.
- Proposed recovery point objective (RPO): no more than 24 hours of data loss.
- Proposed recovery time objective (RTO): restore essential service within 8 hours of disaster declaration.
- Proposed rolling backup retention: 30 days, reconciled with legal, contractual, child-data retention, and deletion obligations before adoption.
- Use point-in-time recovery where needed to meet approved objectives; document its actual recovery window.
- Encrypt backups in transit and at rest, restrict access to recovery personnel, and separate backup administration from ordinary application access where feasible.
- Maintain an isolated or immutable recovery copy where provider capabilities permit; document residual risk if unavailable.
- Do not store recovery secrets in public repositories or alongside unrestricted backup copies.

Define tighter or different objectives per critical workflow/customer where justified. Owner approval and measured exercises are required before publishing availability or recovery promises. Document key recovery without exposing secret values.

## Backup operations

1. Configure and verify coverage for every inventory item. Identify unsupported assets explicitly.
2. Monitor each scheduled backup, investigate missed/failed jobs, and verify alert delivery to the responsible role.
3. Record execution time, source, backup identity, coverage, encryption/access evidence, result, and exception disposition.
4. Review backup-job results daily and coverage/permissions monthly. Record reviews and changes.
5. Protect backups and logs from unauthorized alteration or deletion. Test expiration and reconcile legal holds.
6. Reassess recovery requirements before migrations, storage changes, or material releases.

## Restore procedure and validation

1. Declare the incident/exercise; identify source backup, recovery timestamp, target environment, exact application version, recovery owner, and objectives.
2. Restore to an isolated authorized environment. Use synthetic data for routine engineering tests; if genuine production recovery data is needed, apply production-equivalent access and privacy restrictions.
3. Recover database, files, configuration, and required dependencies together. Verify encryption-key access and backup compatibility.
4. Check schema/migrations, tenant boundaries, authentication/authorization, file access, key workflows, row/count or checksum reconciliation where appropriate, and finance reconciliation without enabling payment processing.
5. Measure actual elapsed recovery time and the latest recovered transaction timestamp. Calculate RTO/RPO performance; do not infer results from a successful restore command.
6. Record failures and corrective actions; retest before closure. Obtain owner approval before directing live traffic to the restored environment.
7. Remove temporary recovery environments and privileges under the approved retention rules; preserve sanitized exercise evidence.

Perform a sampled restore at least quarterly and a complete service-recovery exercise annually and after material recovery-architecture changes. Before the first operational production claim, complete an end-to-end restore exercise for the selected deployment.

## Deletion, legal holds, and records

Document how customer deletion propagates to backups. Where selective backup deletion is not feasible, specify bounded expiration, restricted access, and reapplication of deletion requests before restored data is made live. Do not promise immediate permanent deletion while retrievable backup copies remain. Approved legal holds must identify authority, scope, reviewer, and release conditions.

Retain restricted backup/restore review and exercise evidence for a proposed minimum of 12 months, extended for contracts, legal holds, or auditor requirements. This evidence period is separate from customer-data backup retention.

## Closure conditions

Operational closure requires approved objectives/retention, complete inventory, configuration and encryption/access evidence, tested failure alerts, measured restore results meeting approved objectives, deletion/hold handling, and resolved or formally accepted exceptions. Policy completion alone does not demonstrate recoverability.
