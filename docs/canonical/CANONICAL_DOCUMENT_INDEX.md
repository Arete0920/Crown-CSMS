# CROWN Canonical Document Index

**Status:** Canonical documentation authority
**Last verified:** 2026-09-27
**Current repository identity:** resolve exact current `refs/heads/main` from Git/GitHub; do not duplicate a mutable self-invalidating SHA in this index

This index defines the active documentation authority surface for Crown-CSMS. Exact source identity must be resolved from Git/GitHub and recorded in the immutable evidence packet or release/transfer record for the decision being made.

| Document | Purpose | Authority source | Review trigger |
|---|---|---|---|
| `README.md` | Repository orientation and engineering posture | This index; current release status | Each release-authority change |
| `docs/INVESTOR_TECHNICAL_REVIEW_GUIDE.md` | Investor technical diligence navigation | Current release status; diligence evidence index | Each material diligence/release change |
| `docs/README.md` | Documentation navigation | This index | Documentation-structure change |
| `docs/canonical/REPOSITORY_MANIFEST.md` | Allowed active repository surface | This index | Repository-structure change |
| `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md` | Diligence navigation and evidence boundary | Current release status | Each release or handoff decision |
| `docs/CURRENT_RELEASE_STATUS.md` | Current release, payment, recovery, and turnover posture | Exact Crown-CSMS evidence; authorized decision | Every release-relevant change |
| `docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md` | Historical certification record for the August 18, 2026 baseline | Exact evidence retained with that baseline | Material certification change |
| `docs/architecture/ARCHITECTURE_MAP.md` | Current architecture | Implemented source; accepted decisions | Architecture/ownership change |
| `docs/architecture/DECISION_INDEX.md` | Architecture decision navigation | Accepted decision records | Each architecture decision |
| `docs/engineering/DEV_SETUP.md` | Reproducible engineering setup | Current repository configuration | Setup/dependency change |
| `docs/governance/CHANGE_MANAGEMENT.md` | Change, evidence, approval, rollback policy | Repository governance | Governance-policy change |
| `docs/governance/GITHUB_REPOSITORY_ADMINISTRATION_BASELINE.md` | Intended GitHub administration controls and quarterly review | Repository governance | GitHub administration/security change |
| `docs/governance/PUBLIC_REPOSITORY_LICENSING_DECISION.md` | Public-repository licensing boundary | Owner business/legal decision | Licensing/distribution decision |
| `docs/governance/GITHUB_REPOSITORY_ADMINISTRATION_BASELINE.md` | Intended GitHub administration controls and quarterly review | Repository governance | GitHub administration/security change |
| `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md` | Human authority and engineering accountability | Founder/Product Owner policy | Policy change |
| `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md` | Evidence-backed attribution | Durable contribution evidence | Attribution change |
| `docs/engineering/CODE_QUALITY_AND_REPOSITORY_HYGIENE_STANDARD.md` | Code-quality and repository-hygiene controls | Repository governance | Quality policy change |
| `docs/engineering/REPOSITORY_WORKFLOW.md` | Repository work contract | Repository governance | Workflow/policy change |
| `docs/engineering/VERSIONING_AND_RELEASE_POLICY.md` | Semantic versioning, immutable source identity, and release-tag discipline | Release governance | Versioning/release-policy change |
| `docs/engineering/NAMING_AND_IDENTIFIER_STANDARD.md` | Product, code, route, branch, migration, and compatibility naming rules | Repository governance | Naming/identifier-policy change |
| `docs/engineering/CI_ARCHITECTURE.md` | CI gate families and consolidation rules | Repository governance | CI architecture change |
| `docs/engineering/VERSIONING_AND_RELEASE_POLICY.md` | Semantic versioning, immutable source identity, and release-tag discipline | Release governance | Versioning/release-policy change |
| `docs/operations/SCHOOL_IMPLEMENTATION_RUNBOOK.md` | Contract-to-go-live school implementation authority | Operations | Implementation-process change |
| `docs/operations/README.md` | Operations navigation | Current operational controls | Operational-control change |
| `docs/ownership/OWNER_HANDOFF.md` | Controlled ownership transfer | Current release status; successor acceptance | Each handoff-stage change |
| `docs/KNOWN_LIMITATIONS.md` | Disclosed product/operational limits | Verified evidence; accepted risk | Each material limitation change |
| `SECURITY.md` | Security reporting and baseline | Current security policy | Security-policy change |
| `CONTRIBUTING.md` | Contribution requirements | Change-management policy | Contribution-policy change |

## Exact-identity rule

When exact identity matters, resolve the current Git ref directly and retain the exact SHA in immutable evidence. Historical copied SHAs may remain as provenance when clearly labeled historical, but they must not be represented as current `main`.

## Classification and use

- **CURRENT / CANONICAL:** listed above and governed by its stated authority.
- **CONTROLLED SUPPORTING:** linked from a canonical record for a bounded purpose and noncontradictory.
- **HISTORICAL:** predecessor/provenance only; never current operating authority.
- **STALE / CONTRADICTORY:** conflicts with current authority; do not rely on it.
- **DUPLICATE:** repeats an authority without a defined supporting role.
- **UNSUPPORTED:** lacks exact evidence or an authorized decision.

## Repository hygiene rule

Active onboarding, diligence, operations, and owner-facing material must align with the current release status. Historical release boards, copied conversations, generated proof dumps, obsolete completion claims, superseded repository paths, and old SHAs must not be presented as current authority.
