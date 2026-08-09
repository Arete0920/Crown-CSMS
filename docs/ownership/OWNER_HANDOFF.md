# CROWN Owner Handoff

**Status:** Canonical transfer guide  
**Last reconciled:** 2026-08-09  
**Certified backend:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`  
**Immutable tag:** `prod-deploy-20260808-ce12c95`  
**Controlling authority:** GitHub issue #1619

## Current posture

CROWN has a bounded certified production release. Actual ownership turnover remains pending an identified buyer, buyer acceptance, successor-controlled accounts, approved access transfer, credential rotation, and seller-access removal. Payment processing remains disabled and fail closed.

## Transfer sequence

1. Verify issue #1619 and `docs/CURRENT_RELEASE_STATUS.md`.
2. Resolve the immutable tag to the certified backend SHA.
3. Review production run `31287503791`, dashboard run `31289219093`, and the retained certification artifact.
4. Review architecture, security, operations, privacy, limitations, provenance, and dependency records.
5. Identify the successor and record acceptance of the certified scope and disclosed boundaries.
6. Create successor-controlled accounts before removing seller access.
7. Transfer repository, cloud, domain, certificate, monitoring, backup, vendor, contract, and billing authority.
8. Rotate credentials, keys, tokens, webhooks, certificates, and recovery codes.
9. Verify clean-clone setup, tests, build, deployment authority, monitoring, and any transaction-required recovery exercises.
10. Update `CODEOWNERS`, repository rules, environment approvers, contacts, and notifications.
11. Record final acceptance, exceptions, residual risks, and seller-access removal.

Repository history includes diagnostic, superseded, and temporary release-control pull requests. They remain immutable engineering provenance but do not define the current operating model. Current work follows `docs/governance/CHANGE_MANAGEMENT.md`: one coherent, independently reversible outcome per pull request.
