# CROWN Investor Technical Review Guide

**Purpose:** Provide a concise, evidence-based path for technical diligence.

## What this repository demonstrates

CROWN is a multi-tenant Christian school management platform with documented architecture, tenant boundaries, authorization controls, release governance, automated test coverage, security scanning, dependency management, recovery procedures, and an active compliance-readiness program.

## Recommended review sequence

### 1. Product and release posture
Read:
- `README.md`
- `docs/CURRENT_RELEASE_STATUS.md`
- `docs/PUBLIC_REPO_STATUS.md`
- `docs/engineering/BUYER_REVIEW_PREPARATION_20261004.md`
- `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md`

These documents define the current authoritative line, verified repository controls, active diligence exceptions, what is historical, and what remains environment-specific. Closed or superseded PRs and stale workflow runs are historical engineering records, not current release authority.

### 2. Architecture and ownership
Read:
- `docs/architecture/ARCHITECTURE_MAP.md`
- `docs/architecture/DECISION_INDEX.md`
- `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`

Focus on:
- tenant isolation;
- canonical data ownership;
- authentication and RBAC;
- integration boundaries;
- deployment identity;
- recovery design.

### 3. Security controls
Read:
- `SECURITY.md`
- current CI workflow results;
- dependency, secret-scan, CodeQL, tenant-isolation, schema, and release gates.

Important boundary: repository controls do not by themselves prove the state of a specific deployed production environment.

### 4. Engineering discipline
Read:
- `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md`
- `docs/engineering/REPOSITORY_WORKFLOW.md`
- `docs/engineering/CODE_QUALITY_AND_REPOSITORY_HYGIENE_STANDARD.md`
- `docs/engineering/DEV_SETUP.md`

Evaluate:
- change isolation;
- exact-head verification;
- rollback discipline;
- testing;
- dependency management;
- documented limitations.

### 5. Operations and resilience
Read:
- `docs/operations/README.md`
- disaster recovery and restore procedures referenced there.

Distinguish proven engineering mechanics from environment-specific production exercises.

### 6. Implementation repeatability
Read:
- `docs/operations/SCHOOL_IMPLEMENTATION_RUNBOOK.md`

Evaluate whether contract intake, data mapping, tenant provisioning, migration, training, go-live, hypercare, and operational handoff form one repeatable process rather than founder-specific knowledge.

### 7. Compliance readiness
Read:
- `docs/compliance/PRIVACY_COMPLIANCE_EVIDENCE_STATUS.md`
- the active SOC 2/student-privacy readiness materials when merged.

CROWN does not claim independent SOC 2 attestation or legal certification solely from repository controls.

## Questions an investor should be able to answer after review

1. Is the product architecture coherent and maintainable?
2. Are school/tenant boundaries explicit and tested?
3. Are authentication and authorization fail-closed?
4. Are source changes controlled and reversible?
5. Are dependency and security vulnerabilities actively managed?
6. Are critical product and financial workflows tested?
7. Are release claims tied to exact source identity?
8. Are known limitations disclosed rather than hidden?
9. Is there a credible path to production operations and SOC 2 readiness?
10. Can the product scale without creating tenant-specific forks?

## Current review statement

CROWN is appropriate for technical and investment diligence review. Review should be anchored to the current protected `main` line and its exact-head evidence rather than historical branch state. Production deployment evidence, customer contracts, payment-provider activation, external generative-AI activation, legal/privacy applicability, and independent audit attestations should be reviewed as separate diligence workstreams.
