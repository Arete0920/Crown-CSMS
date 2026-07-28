# CROWN Canonical Document Index

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Authority rule

A document is authoritative only when listed here as `CANONICAL`, or when a later approved decision explicitly supersedes it. Unlisted documents may be supporting evidence, history, drafts, or generated output, but they do not override canonical authority.

## Canonical documents

| Subject | Document | Status |
|---|---|---|
| Repository orientation | `README.md` | CANONICAL |
| Repository structure | `docs/canonical/REPOSITORY_MANIFEST.md` | CANONICAL |
| Developer setup | `docs/engineering/DEV_SETUP.md` | CANONICAL |
| Documentation navigation | `docs/README.md` | CANONICAL |
| Operations navigation | `docs/operations/README.md` | CANONICAL OPERATIONS GATEWAY |
| Current release posture | `docs/CURRENT_RELEASE_STATUS.md` | CANONICAL RELEASE/FREEZE AUTHORITY |
| Security reporting | `SECURITY.md` | CANONICAL |
| Contribution rules | `CONTRIBUTING.md` | CANONICAL, review during ownership transfer |
| Code ownership | `CODEOWNERS` | CANONICAL, successor update required |
| Repository work controls | `AGENTS.md` | CANONICAL ENGINEERING CONTROL |

## Controlled supporting records

| Subject | Document | Status |
|---|---|---|
| Technical diligence overview | `docs/investor/README.md` | CONTROLLED SUPPORTING; release posture remains governed by `docs/CURRENT_RELEASE_STATUS.md` |
| Development provenance | `docs/provenance/CROWN_DEVELOPMENT_PROVENANCE.md` | CONTROLLED SUPPORTING; truthful lineage, not architecture or release authority |
| Repository noise inventory | `docs/repo-cleanup/REPOSITORY_NOISE_INVENTORY_20260728.md` | CONTROLLED HISTORICAL CLEANUP RECORD |

## Supporting and historical areas requiring reconciliation

| Subject | Document or area | Status |
|---|---|---|
| System context | `docs/architecture/` | CONSOLIDATION REQUIRED |
| Current operations material | `docs/operations/` | CONTROLLED BY `docs/operations/README.md` |
| Legacy operations material | `docs/ops/` | LEGACY SUPPORTING; INVENTORY REQUIRED |
| Historical development records | historical commits, pull requests, branches, comments, and retained tool-specific records | HISTORICAL PROVENANCE; excluded from onboarding and active authority |
| Release evidence | `docs/release/evidence/` | GENERATED OR SUPPORTING EVIDENCE |
| Completion snapshots | `docs/completion/` | MIXED AGE; NOT CURRENT AUTHORITY |
| Audit output | `audit-artifacts/` | GENERATED EVIDENCE |
| Cleanup reports | `docs/repo-cleanup/` | HISTORICAL; NOT RELEASE AUTHORITY |

## Onboarding boundary

The normal onboarding and diligence path must not direct readers to obsolete editor-specific, assistant-specific, prompt-specific, agent-session, retired certification, or superseded release-control files. Such records may be retained only where needed for provenance, security, audit, or historical lineage and must not be represented as current engineering requirements.

## Classification labels

- `CANONICAL` — current authority.
- `SUPPORTING` — useful detail consistent with canonical authority.
- `CONTROLLED SUPPORTING` — approved orientation or provenance material that does not override release, security, architecture, or operational authority.
- `HISTORICAL` — retained to preserve prior decisions, lineage, or evidence.
- `SUPERSEDED` — replaced by a named canonical document.
- `GENERATED_EVIDENCE` — machine-produced output, not narrative authority.
- `OBSOLETE` — no longer useful after required preservation.

## Change control

Changing canonical authority requires a focused, evidence-backed change that names the document being replaced, explains the reason, identifies conflicts resolved, updates this index, and preserves required historical evidence.

## Ownership-transfer note

`CODEOWNERS`, repository administrator access, external service ownership, contributor records, domains, certificates, cloud resources, secrets, and operating authority must be updated with verified identities and actual responsibilities during an authorized handoff. Names or roles must not be invented.
