# CROWN Repository Migration Canon

**Status:** REPOSITORY CUTOVER COMPLETE; CONTENT RECONCILIATION AND OWNER HANDOFF IN PROGRESS  
**Last verified:** 2026-08-13

## Authority

Crown-CSMS is the active engineering and owner-turnover repository. Crown2026 remains the preserved historical predecessor and rollback/provenance source. Migration does not transfer production certification, buyer acceptance, or completed-turnover status.

## Operating rules

- Verify exact source and destination SHAs before relying on migration or release claims.
- Preserve Crown2026 history; do not delete, rewrite, or cosmetically erase provenance.
- Classify active material as KEEP, MERGE, UPDATE, HISTORICAL, DROP, or REVIEW.
- Do not convert UNKNOWN or NOT VERIFIED into PASS.
- Do not imply reviews, approvals, contributors, or teams that did not exist.
- Keep active documentation concise, current, nonduplicative, and tool-neutral unless a named tool is operationally material.
- Automated assistance is not independent human review or approval.
- Do not carry secrets, credentials, generated proof dumps, copied conversations, local-machine paths, obsolete automation, or superseded operating instructions into the buyer-facing authority surface.

## Separate gates

Repository cutover, content hygiene, release certification, deployed-runtime identity, buyer diligence readiness, and operational turnover are separate gates. Crown-CSMS currently requires further hygiene and exact-identity handoff proof under `docs/CURRENT_RELEASE_STATUS.md`.

## Verification and rollback

For each remediation record the exact base/head, affected paths, validation, limitations, decision owner, and rollback. Crown2026 remains immutable historical provenance. Crown-CSMS changes use bounded reversible pull requests.

## Qualified-review boundary

Legal, tax, accounting, transaction, valuation, contractual, insurance, privacy, accessibility, security, and payment-provider conclusions require the appropriate qualified reviewers and cannot be resolved by documentation cleanup.

## Completion criteria

Owner-handoff readiness requires:

1. canonical and supporting records reconciled;
2. stale, contradictory, duplicate, historical, and unsupported active material dispositioned;
3. critical product and owner-visible blockers resolved;
4. one exact Crown-CSMS source/deployment/runtime identity verified;
5. applicable CI, security, tenant, permission, accessibility, rollback, restore, monitoring, and operational evidence complete;
6. authorized human release and acceptance decisions recorded;
7. buyer-specific transfer and seller-access removal completed.

Material migration decisions remain recorded in `docs/handoff/CROWN_MIGRATION_DECISION_LOG.md`.
