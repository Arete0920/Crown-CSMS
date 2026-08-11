# CROWN Repository Migration Canon

Status: PREPARATION / NOT YET CUT OVER

This document is the controlling specification for preparation and execution of the planned CROWN successor-repository migration. It exists to prevent scope drift, stale material, duplicate work, unsupported assumptions, and loss of institutional knowledge.

## 1. Operating rule

Before migration work begins in any session:
1. Read this document.
2. Verify the current authoritative `Crown2026` `main` SHA.
3. Review the current migration decision log and file inventory when those artifacts exist.
4. Verify open PR, issue, and certification state from GitHub.
5. Do not treat historical chat, stale evidence, or an earlier SHA as current truth.

At the end of each migration work session:
1. Record the exact source and destination SHAs involved.
2. Update file dispositions and unresolved items.
3. Record material migration decisions and their evidence.
4. Re-verify that no critical requirement was silently dropped.

## 2. Current source repository

Source repository: `tcmegahan/Crown2026`
Authoritative branch: `main`
Preparation baseline observed when this Canon was created: `48b2ac7d595366384df68e5a11b39a003d1f2b6c`

The preparation baseline is not automatically the final migration baseline. The final baseline must be recorded only after current hygiene/remediation work is complete and the selected source SHA is verified.

## 3. Migration objectives

The successor repository must provide a clean, professional operating surface while preserving the legitimate CROWN product, Canon, institutional knowledge, and required provenance.

The migration must not be used to:
- hide unfinished critical functionality;
- convert UNKNOWN or NOT VERIFIED items into PASS;
- imply reviews, approvals, contributors, or teams that did not exist;
- discard requirements merely because their documentation is inconvenient;
- import stale repository clutter simply because it exists in the source repository.

## 4. Source-repository preservation and rollback

`Crown2026` remains the historical/archive and rollback source through migration verification. Do not delete, rewrite, or otherwise destroy the source repository as part of normal successor-repository preparation.

A successor repository is not authoritative until its intended source, documentation, configuration, and verification state have been reconciled against the approved migration baseline.

## 5. Pull request and issue hygiene before migration

Before final baseline selection:
- finish legitimate current PR work;
- eliminate redundant deltas rather than carrying duplicate fixes forward;
- close stale/superseded PRs only after verifying they contain no unique unfinished work;
- close issues only when their acceptance criteria are actually satisfied or when a documented disposition makes them no longer applicable;
- avoid creating new PRs solely to work around CI congestion or to generate evidence;
- preserve exact-head verification and current-main synchronization requirements.

The target successor-repository handoff state is zero stale/redundant PRs and zero stale/redundant issues. Any remaining open item must represent real, current, explicitly documented work.

## 6. File migration classification

Every significant tracked file or document considered for the successor repository receives one disposition:

- **KEEP** — current, authoritative, necessary.
- **MERGE** — overlapping/duplicate content consolidated into one authoritative destination without losing requirements or institutional knowledge.
- **UPDATE** — valid material requiring current terminology, status, paths, ownership, dates, or implementation alignment.
- **ARCHIVE** — historically useful but not appropriate for the successor repository's active surface. `Crown2026` may serve as the archive rather than copying an archive directory forward.
- **DROP** — temporary, generated, testing-only, obsolete, redundant, nonsensical, superseded, or otherwise unnecessary material.
- **REVIEW** — uncertain provenance, authority, or continuing value; do not migrate until resolved.

No Canon document may be dropped or merged solely on filename similarity. Canon consolidation requires content comparison and confirmation that all active requirements survive.

## 7. Canon and documentation protection

Canonical material must be inventoried before cutover. At minimum review:
- `docs/canonical/`;
- architecture documentation;
- governance and requirement-to-evidence material;
- security and tenant-isolation documentation;
- module, dashboard, wizard, role/permission, sandbox, deployment, operations, and handoff documentation;
- repository manifests and indexes.

Canonical indexes and repository manifests are evidence sources for the inventory, not automatic proof that every referenced file remains current.

## 8. Documentation hygiene

Aggressively review for:
- duplicate or contradictory Canon documents;
- obsolete audit/status reports;
- timestamped certification snapshots;
- generated evidence and test output;
- stale buyer/handoff drafts;
- superseded architecture or release plans;
- one-time proof files;
- abandoned experiments;
- obsolete scripts;
- old screenshots, traces, logs, and test reports better retained as workflow artifacts;
- stale terminology and references to superseded workflows, repository names, branches, or product naming.

The successor repository should contain material an incoming engineer needs to understand, operate, test, secure, deploy, maintain, and extend CROWN—not a historical dump of every remediation artifact.

## 9. Terminology and automated-assistance guidance

Current documentation should use neutral, accurate engineering terminology where a specific tool name is not materially relevant. Unnecessary tool-centric language may be normalized to terms such as automated review, automated analysis, repository tooling, CI verification, static analysis, or engineering assistance when those terms accurately describe the process.

Do not falsify provenance or imply human authorship, independent review, approval, or certification that did not occur. Automated assistance is not approval authority.

Before broad terminology cleanup, recover and verify the previously established CROWN terminology guidance and use the authoritative version consistently rather than inventing a replacement standard during migration.

## 10. Repository operating surface

The successor repository should begin with a deliberately minimal active surface:
- one authoritative protected `main` branch;
- no stale branches;
- no inherited historical PR or issue database unless deliberately recreated as current work;
- only current tags/releases that have continuing operational value;
- current documentation and configuration only;
- generated evidence retained in workflow artifacts or designated evidence systems rather than committed as repository noise where practical.

## 11. Governance

Do not fabricate CODEOWNERS, development teams, reviewers, or approval structures.

Until real independent reviewers with individual GitHub identities and defined responsibilities exist, governance should rely on accurate maintainer identity, protected branches, required CI, security controls, explicit merge criteria, and documented independent-review workarounds where genuinely applicable.

No self-approval is asserted. Automated assistance is not approval authority.

## 12. CI and workflow design

Do not reproduce unnecessary workflow fan-out in the successor repository.

Target architecture:
- changed-file/scope classification;
- focused backend checks when backend changes;
- focused frontend checks when frontend changes;
- migration/schema checks when database structure changes;
- dependency/security checks when dependencies change;
- focused sandbox proof when sandbox surfaces change;
- full release certification for integration/release candidates.

Consolidate overlapping gates where doing so preserves or improves verification strength. Never reduce required verification merely to make CI faster or cosmetically greener.

## 13. Security baseline

Before cutover verify appropriate repository security controls, including branch/ruleset protections, dependency visibility and alerts, secret handling/scanning where available, code/security scanning where appropriate, least-privilege access, and removal of obsolete credentials/configuration from the successor repository.

Do not carry secrets, local credentials, tokens, private keys, or environment-specific sensitive values into the successor repository.

## 14. Certification and product readiness

Migration cleanliness and product readiness are separate gates.

The successor repository must not be described as fully verified merely because migration succeeded. Critical functionality, sandbox buyer journeys, role/permission boundaries, tenant isolation, backend/frontend quality, security, routes, deployment/runtime behavior, and release/handoff controls require fresh evidence against the selected migration baseline or its verified successor equivalent.

Known P0/P1 defects and critical UNKNOWN/NOT VERIFIED items must be resolved or explicitly dispositioned before owner handoff.

## 15. Equivalence and integrity proof

For the final migration baseline, record:
- source repository;
- source branch;
- source SHA;
- migration method;
- intended exclusions/transformations;
- destination repository;
- destination baseline SHA;
- source-tree equivalence results for material intended to transfer;
- documentation inventory results;
- configuration/workflow reconciliation results;
- certification results.

Any intentional difference between source baseline and destination baseline must be explainable by an approved migration disposition.

## 16. Companion control artifacts

The migration process should maintain:
- `docs/handoff/CROWN_MIGRATION_FILE_INVENTORY.csv`
- `docs/handoff/CROWN_MIGRATION_DECISION_LOG.md`

Recommended inventory columns:
`Path,Type,Current,Canon,Disposition,Destination,DuplicateOf,TerminologyReview,Verified,Notes`

The decision log records date, decision, rationale, evidence, affected paths/scope, and resulting SHA/state.

## 17. Cutover gate

Do not designate the successor repository authoritative until all applicable cutover checks are PASS, including:
- approved final source baseline recorded;
- current legitimate PR queue reconciled;
- stale/redundant issues removed;
- Canon inventory completed;
- file migration inventory completed;
- required terminology cleanup completed;
- successor repository structure reviewed;
- CI/security/governance configuration verified;
- intended source/configuration equivalence verified;
- fresh certification completed at the approved baseline;
- no hidden critical UNKNOWN or unresolved P0/P1 blocker;
- rollback/archive source preserved.

## 18. Decision authority

This Canon controls migration execution unless a later explicit, evidence-backed decision updates it. Material changes to migration method, preservation policy, Canon handling, certification requirements, or cutover criteria must be recorded in the migration decision log rather than silently changing operating practice.
