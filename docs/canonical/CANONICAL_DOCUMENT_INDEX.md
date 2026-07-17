# CROWN Canonical Document Index

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-17

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
| Current release posture | `docs/CURRENT_RELEASE_STATUS.md` | CANONICAL RELEASE AUTHORITY |
| Security reporting | `SECURITY.md` | CANONICAL |
| Contribution rules | `CONTRIBUTING.md` | CANONICAL, review during ownership transfer |
| Code ownership | `CODEOWNERS` | CANONICAL, successor update required |
| Technical diligence overview | `docs/investor/README.md` | CONTROLLED SUPPORTING; release posture remains governed by `docs/CURRENT_RELEASE_STATUS.md` |
| Repository work controls | `AGENTS.md` | CANONICAL ENGINEERING CONTROL |

## Supporting documents requiring reconciliation

| Subject | Document or area | Status |
|---|---|---|
| System context | `docs/architecture/` | CONSOLIDATION REQUIRED |
| Current operations material | `docs/operations/` | CONTROLLED BY `docs/operations/README.md` |
| Legacy operations material | `docs/ops/` | LEGACY SUPPORTING; INVENTORY REQUIRED |
| Historical development provenance | `docs/provenance/` | HISTORICAL/SUPPORTING |
| Release evidence | `docs/release/evidence/` | GENERATED OR SUPPORTING EVIDENCE |
| Completion snapshots | `docs/completion/` | MIXED AGE; NOT CURRENT AUTHORITY |
| Audit output | `audit-artifacts/` | GENERATED EVIDENCE |
| Cleanup reports | `docs/repo-cleanup/` | HISTORICAL |

## Classification labels

- `CANONICAL` — current authority.
- `SUPPORTING` — useful detail consistent with canonical authority.
- `CONTROLLED SUPPORTING` — approved orientation material that does not override release, security, architecture, or operational authority.
- `HISTORICAL` — retained to preserve prior decisions or evidence.
- `SUPERSEDED` — replaced by a named canonical document.
- `GENERATED_EVIDENCE` — machine-produced output, not narrative authority.
- `OBSOLETE` — no longer useful after required preservation.

## Change control

Changing canonical authority requires a focused pull request that names the document being replaced, explains the reason, identifies conflicts resolved, updates this index, preserves required historical evidence, and receives human review.

## Ownership-transfer note

`CODEOWNERS`, repository administrator access, external service ownership, contributor records, domains, certificates, cloud resources, secrets, and operating authority must be updated with verified identities and actual responsibilities during the handoff session. Names or roles must not be invented.
