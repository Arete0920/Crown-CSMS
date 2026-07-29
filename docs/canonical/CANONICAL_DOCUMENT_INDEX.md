# CROWN Canonical Document Index

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Authority rule

A document is authoritative only when listed here as `CANONICAL`, or when a later approved decision explicitly supersedes it. Unlisted documents do not override canonical authority.

## Canonical documents

| Subject | Document | Status |
|---|---|---|
| Repository orientation | `README.md` | CANONICAL |
| Repository structure | `docs/canonical/REPOSITORY_MANIFEST.md` | CANONICAL |
| Documentation navigation | `docs/README.md` | CANONICAL |
| Developer setup | `docs/engineering/DEV_SETUP.md` | CANONICAL |
| Architecture | `docs/architecture/` | CANONICAL TECHNICAL AREA |
| Operations | `docs/operations/README.md` | CANONICAL OPERATIONS GATEWAY |
| Owner transfer | `docs/ownership/OWNER_HANDOFF.md` | CANONICAL TRANSFER GUIDE |
| Current release posture | `docs/CURRENT_RELEASE_STATUS.md` | CANONICAL RELEASE/FREEZE AUTHORITY |
| Security reporting | `SECURITY.md` | CANONICAL |
| Contribution rules | `CONTRIBUTING.md` | CANONICAL |
| Code ownership | `CODEOWNERS` | CANONICAL; update during authorized transfer |
| Repository work controls | `AGENTS.md` | CANONICAL ENGINEERING CONTROL |

## Controlled supporting records

| Subject | Document | Status |
|---|---|---|
| Development provenance | `docs/provenance/CROWN_DEVELOPMENT_PROVENANCE.md` | CONTROLLED SUPPORTING; lineage only |

## Active repository boundary

The owner-facing repository should contain only:

- application source and migrations;
- active tests and build configuration;
- current CI and deployment definitions;
- architecture, engineering, security, operations, and ownership-transfer documentation;
- dependency, license, provenance, and governance files required to understand or operate the software;
- the current release/freeze authority.

Generated audit output, test-result dumps, copied evidence packs, marketing material, transaction strategy, old demonstrations, obsolete completion systems, superseded release boards, cleanup working notes, and retired scripts are excluded from the active tree.

## Onboarding boundary

Normal onboarding must not direct readers to editor-specific, assistant-specific, prompt-specific, agent-session, retired certification, superseded release-control, or historical proof material. Historical commits and pull requests remain provenance but are not active operating instructions.

## Classification labels

- `CANONICAL` — current authority.
- `CANONICAL TECHNICAL AREA` — current technical documentation governed by this index.
- `CONTROLLED SUPPORTING` — useful information that does not override release, security, architecture, or operational authority.
- `HISTORICAL` — repository history only; not active navigation.
- `OBSOLETE` — removed from the current tree.

## Change control

Changes to canonical authority require a focused review that names the document being replaced, explains the reason, identifies conflicts resolved, and updates this index.

## Ownership-transfer note

Repository administration, `CODEOWNERS`, external services, domains, certificates, cloud resources, secrets, operating authority, and notification destinations must be updated with verified successor identities during an authorized handoff. Secret values must never be committed.
