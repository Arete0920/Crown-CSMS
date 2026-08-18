# CROWN Canonical Document Index

**Status:** Canonical documentation authority
**Last verified:** 2026-08-18
**Current certified handoff base `main`:** `8d3f364180d6a0360228c7d72ace4fa7b54e1dc2`

This index defines the active documentation authority surface for Crown-CSMS. It intentionally does **not** embed per-file blob SHAs as durable authority because those IDs become stale whenever a governed document is updated. Exact source identity belongs in the current release/status record and the Git history for the reviewed change.

| Document | Purpose | Authority source | Review trigger |
|---|---|---|---|
| `README.md` | Repository orientation and claim boundary | This index; current release status | Each handoff/release-authority change |
| `docs/README.md` | Documentation navigation | This index | Documentation-structure change |
| `docs/canonical/REPOSITORY_MANIFEST.md` | Allowed active repository surface | This index | Repository-structure change |
| `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md` | Diligence navigation and evidence boundary | Current release status | Each handoff/release decision |
| `docs/CURRENT_RELEASE_STATUS.md` | Current release status; Release, freeze, payment, and turnover posture | Exact Crown-CSMS evidence; authorized decision | Every release-relevant change |
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

## Classification and use

- **CURRENT / CANONICAL:** listed above and governed by its stated authority.
- **CONTROLLED SUPPORTING:** linked from a canonical record for a bounded purpose and noncontradictory.
- **HISTORICAL:** predecessor/provenance only; never current operating authority.
- **STALE / CONTRADICTORY:** conflicts with current authority; do not rely on it.
- **DUPLICATE:** repeats an authority without a defined supporting role.
- **UNSUPPORTED:** lacks exact evidence or an authorized decision.

Predecessor-repository material is historical provenance material for Crown-CSMS unless a current canonical record explicitly incorporates a bounded fact from it.

## Owner-handoff hygiene rule

Active onboarding, diligence, operations, and owner-facing material must be concise, current, nonduplicative, and explicit about evidence boundaries. Historical release boards, copied conversations, generated proof dumps, obsolete completion claims, retired automation instructions, superseded repository paths, and old SHAs must not be presented as current authority.

If a current fact changes, update the governing canonical record first; supporting documents must reference that authority rather than duplicating mutable status claims wherever practical.