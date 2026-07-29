# CROWN Owner Handoff

**Status:** Canonical transfer guide  
**Scope:** Repository, application, operations, security, and external-service ownership

## Current operating posture

CROWN remains frozen and is not production-authorized. Buyer operational turnover and external payment processing are not approved. The controlling status is `docs/CURRENT_RELEASE_STATUS.md`.

This guide describes the ownership-transfer process. It does not authorize deployment, production use, payment activation, or release.

## Repository start path

1. `README.md`
2. `docs/canonical/REPOSITORY_MANIFEST.md`
3. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`
4. `docs/engineering/DEV_SETUP.md`
5. `docs/architecture/`
6. `docs/security/`
7. `docs/operations/README.md`
8. `docs/CURRENT_RELEASE_STATUS.md`

## What transfers with the repository

- application source and migrations;
- backend and frontend tests;
- CI and deployment definitions;
- architecture and engineering documentation;
- security policy and security-control definitions;
- operational, rollback, restore, maintenance, and incident-response documentation;
- dependency and lock files;
- repository history, issues, pull requests, and release lineage.

## External ownership that must be transferred separately

The repository must not contain secret values. The authorized transfer process must separately assign and verify:

- GitHub repository or organization administrator authority;
- branch rules, environments, required checks, Actions secrets, variables, and deployment approvals;
- Azure subscriptions, resource groups, applications, service principals, managed identities, Key Vaults, databases, storage, monitoring, and billing ownership;
- domains, DNS, TLS certificates, email, Microsoft 365, and Entra registrations;
- payment-processor, communications, analytics, support, and other integration accounts;
- backup locations, recovery credentials, alert destinations, and incident contacts;
- trademarks, product names, contracts, licenses, and other intellectual-property records.

## Required transfer controls

1. Inventory current administrators and external service owners.
2. Add the authorized successor before removing the prior owner.
3. Rotate credentials, keys, certificates, tokens, webhooks, and recovery codes.
4. Update `CODEOWNERS`, repository rules, environment approvers, security contacts, and notification destinations.
5. Verify that no personal workstation paths or personal credentials are required.
6. Confirm dependency licenses, third-party notices, media licenses, and code-assignment records.
7. Confirm that tracked data is synthetic and that no real school, student, family, employee, payment, health, or confidential customer data is present.
8. Perform a clean clone and complete setup without undocumented assistance.
9. Run the required backend, frontend, migration, security, dependency, and build checks on one exact commit.
10. Complete rollback and restore exercises before production authorization.

## Release restart

A future release restart requires:

- explicit authorization from the then-current owner;
- one immutable release-candidate commit;
- current exact-commit CI and security results;
- authenticated tenant and RBAC verification;
- secrets and historical-key retirement verification;
- rollback and restore proof;
- exact-commit deployment and monitoring proof;
- privacy, legal, licensing, and operational reconciliation;
- a new documented GO/NO-GO decision.

## Claim boundary

Repository transfer does not establish production readiness, regulatory compliance, security certification, recovery certification, or customer suitability. Those claims require current evidence on the exact transferred and deployed release identity.
