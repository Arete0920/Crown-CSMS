# CROWN Canonical Document Index

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-14

## Authority rule

A document is authoritative only when listed here as `CANONICAL` or when a later approved decision explicitly supersedes it. Unlisted documents may be supporting evidence, history, drafts, or generated output, but they do not override canonical authority.

## Canonical documents

| Subject | Document | Status |
|---|---|---|
| Repository orientation | `README.md` | CANONICAL |
| Repository structure | `docs/canonical/REPOSITORY_MANIFEST.md` | CANONICAL |
| Developer setup | `docs/engineering/DEV_SETUP.md` | CANONICAL |
| Documentation navigation | `docs/README.md` | CANONICAL |
| Current release posture | `docs/CURRENT_RELEASE_STATUS.md` | CANONICAL RELEASE AUTHORITY |
| Security reporting | `SECURITY.md` | CANONICAL |
| Contribution rules | `CONTRIBUTING.md` | CANONICAL, review during ownership transfer |
| Code ownership | `CODEOWNERS` | CANONICAL, successor update required |

## Supporting documents requiring reconciliation

| Subject | Document or area | Status |
|---|---|---|
| System context | `docs/architecture/` | CONSOLIDATION REQUIRED |
| Deployment and recovery | `docs/operations/`, `docs/ops/` | CONSOLIDATION REQUIRED |
| Historical development provenance | `docs/provenance/` | HISTORICAL/SUPPORTING |
| Release evidence | `docs/release/evidence/` | GENERATED OR SUPPORTING EVIDENCE |
| Completion snapshots | `docs/completion/` | MIXED AGE; NOT CURRENT AUTHORITY |
| Audit output | `audit-artifacts/` | GENERATED EVIDENCE |
| Cleanup reports | `docs/repo-cleanup/` | HISTORICAL |

## Classification labels

- `CANONICAL` — current authority.
- `SUPPORTING` — useful detail consistent with canonical authority.
- `HISTORICAL` — retained to preserve prior decisions or evidence.
- `SUPERSEDED` — replaced by a named canonical document.
- `GENERATED_EVIDENCE` — machine-produced output, not narrative authority.
- `OBSOLETE` — no longer useful after preservation.

## Change control

Changing canonical authority requires a focused pull request that names the document being replaced, explains the reason, identifies conflicts resolved, updates this index, preserves historical evidence, and receives human review.

## Ownership-transfer note

`CODEOWNERS`, repository administrator access, external service ownership, and contributor records must be updated with verified GitHub usernames and actual responsibilities during the handoff session. Names or roles must not be invented.
