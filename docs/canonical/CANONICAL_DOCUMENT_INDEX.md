# CROWN Canonical Document Index

**Status:** Canonical documentation authority  
**Last verified:** 2026-08-18  
**Current repository identity:** resolve exact current `refs/heads/main` from Git/GitHub; do not duplicate a mutable self-invalidating SHA in this index

This index defines the active documentation authority surface for Crown-CSMS. Exact source identity must be resolved from Git/GitHub and recorded in the immutable evidence packet or transfer/release record for the decision being made.

| Document | Purpose | Authority source | Review trigger |
|---|---|---|---|
| `README.md` | Repository orientation and production-ready posture | This index; current release status | Each handoff/release-authority change |
| `docs/README.md` | Documentation navigation | This index | Documentation-structure change |
| `docs/canonical/REPOSITORY_MANIFEST.md` | Allowed active repository surface | This index | Repository-structure change |
| `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md` | Diligence navigation and evidence boundary | Current release status | Each handoff/release decision |
| `docs/CURRENT_RELEASE_STATUS.md` | Current production-ready engineering, release, payment, recovery, and turnover posture | Exact Crown-CSMS evidence; authorized decision | Every release-relevant change |
| `docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md` | Formal production-ready product/repository engineering certification and claim boundary | Current exact repository evidence; Founder/Product Owner release decision | Material product/security/release regression or certification change |
| `docs/architecture/ARCHITECTURE_MAP.md` | Current architecture | Implemented source; accepted decisions | Architecture/ownership change |
| `docs/architecture/DECISION_INDEX.md` | Architecture decision navigation | Accepted decision records | Each architecture decision |
| `docs/engineering/DEV_SETUP.md` | Reproducible engineering setup | Current repository configuration | Setup/dependency change |
| `docs/governance/CHANGE_MANAGEMENT.md` | Change, evidence, approval, rollback policy | Repository governance | Governance-policy change |
| `docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md` | Human authority and assistance disclosure | Founder/Product Owner policy | Policy change |
| `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md` | Evidence-backed attribution | Durable contribution evidence | Attribution change |
| `docs/engineering/CODE_QUALITY_AND_PROVENANCE_STANDARD.md` | Quality and provenance controls | Repository governance | Quality/provenance policy change |
| `docs/operations/README.md` | Operations navigation | Current operational controls | Operational-control change |
| `docs/ownership/OWNER_HANDOFF.md` | Controlled ownership transfer | Current release status; successor acceptance | Each handoff-stage change |
| `docs/KNOWN_LIMITATIONS.md` | Disclosed product/operational limits | Verified evidence; accepted risk | Each material limitation change |
| `SECURITY.md` | Security reporting and baseline | Current security policy | Security-policy change |
| `CONTRIBUTING.md` | Contribution requirements | Change-management policy | Contribution-policy change |
| `AGENTS.md` | Repository work contract | Repository governance | Workflow/policy change |

## Exact-identity rule

When exact identity matters, resolve the current Git ref directly and retain the exact SHA in immutable evidence. A mutable canonical document must not attempt to prove its own eventual merge SHA. Historical copied SHAs may remain as provenance when clearly labeled historical, but they must not be represented as current `main`.

## Classification and use

- **CURRENT / CANONICAL:** listed above and governed by its stated authority.
- **CONTROLLED SUPPORTING:** linked from a canonical record for a bounded purpose and noncontradictory.
- **HISTORICAL:** predecessor/provenance only; never current operating authority.
- **STALE / CONTRADICTORY:** conflicts with current authority; do not rely on it.
- **DUPLICATE:** repeats an authority without a defined supporting role.
- **UNSUPPORTED:** lacks exact evidence or an authorized decision.

Predecessor-repository material, predecessor issue programs, superseded release campaigns, and obsolete NO-GO scorecards are historical provenance for Crown-CSMS unless a current canonical record explicitly incorporates a bounded fact from them.

## Owner-handoff hygiene rule

Active onboarding, diligence, operations, and owner-facing material must align with the current production-ready engineering certification while preserving the separate transaction-time deployment and operational-transfer boundary. Historical release boards, copied conversations, generated proof dumps, obsolete completion claims, retired automation instructions, superseded repository paths, and old SHAs must not be presented as current authority.
