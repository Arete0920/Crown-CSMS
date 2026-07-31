# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-31  
**Last reviewed:** 2026-07-31  
**Repository baseline reviewed:** `bdc29e9a4f3defe22dee3d57400c18234003775b`

## Authority

This file is the entry point for deployment, release, incident, maintenance, rollback, restore, secret operations, and operational-readiness documentation.

Documents under `docs/operations/` are current operational guidance only when linked from this gateway or explicitly designated canonical by `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`.

Material under `docs/ops/` is legacy supporting material pending file-by-file reconciliation. It may contain useful procedures or historical evidence, but it does not override this gateway, `docs/CURRENT_RELEASE_STATUS.md`, GitHub issue `#1619`, or a later approved runbook.

Release evidence under `docs/release/` supports decisions; it is not, by itself, an operating procedure.

## Mandatory freshness and supersession check

Before any document, process, runbook, issue comment, workflow result, artifact, or historical evidence is used or changed, the reviewer must verify:

1. the document's effective date and last-reviewed date;
2. the exact repository SHA, deployed identity, environment, and workflow version to which it applies;
3. the current controlling issue and whether that authority remains open and applicable;
4. whether a later canonical document, merged PR, runbook, policy, contract, vendor record, or release decision supersedes it;
5. whether referenced tools, dependencies, cloud resources, roles, vendors, credentials, and operational procedures still exist in the current configuration;
6. whether evidence is repository-only, synthetic, pull-request merge-ref, deployed-runtime, or operational evidence;
7. whether an old date or old SHA is being retained only as historical provenance rather than current authority.

If date, source identity, authority, or supersession status is missing or ambiguous, stop and classify the material as `HISTORICAL OR UNVERIFIED` until it is reconciled. Do not silently modernize an old procedure, copy an old result into a current claim, or treat a closed historical issue as proof that its operational acceptance criteria were executed.

## Current posture

CROWN is in bounded remediation before selection of a future immutable release candidate.

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DISABLED AND REQUIRED TO FAIL CLOSED**

Documentation does not prove that a procedure works. Deployment, rollback, restore, secret rotation, break-glass, monitoring, and incident procedures require current execution evidence before production approval.

## Controlling operational lanes

- Lane 3 — rollback, database restore, resilience, and measured RTO/RPO: issue `#1627`
- Lane 4 — secrets, privileged access, rotation, revocation, and break-glass operations: issue `#1628`
- Lane 6 — exact-SHA CI/CD, deployment, infrastructure, observability, and monitoring: issue `#1630`
- Lane 7 — release documentation, runbooks, evidence index, and buyer handoff: issue `#1631`
- Lane 8 — final integrated authorization after all prerequisite lanes pass: issue `#1632`

Closed historical issues such as `#1270`, `#1275`, `#1277`, `#1294`, and `#1296` are context only and are not current operational authorities.

## Required operating flow

A reviewer or successor must be able to follow one documented path through:

1. environment and access prerequisites;
2. configuration and secret dependencies;
3. pre-deployment validation;
4. deployment execution;
5. health and tenant-integrity verification;
6. rollback decision and execution;
7. isolated database restore or manual recovery fallback;
8. incident escalation and evidence capture;
9. monitoring and alert validation;
10. release-authority reconciliation.

## Canonical runbook register

The table below is the required navigation surface. A procedure marked `MISSING OR UNVERIFIED` is an explicit blocker and must not be inferred from historical files.

| Procedure | Canonical runbook | Operator | Required validation | Abort criteria | Evidence output | Status |
|---|---|---|---|---|---|---|
| Deployment | No canonical executable runbook linked yet | Authorized release operator | Exact source, artifact, migration, frontend, and backend identity | Identity mismatch, failed migration, failed health or tenant checks | Deployment log, artifact provenance, runtime SHA proof | **MISSING OR UNVERIFIED** |
| Application rollback | No canonical executable runbook linked yet | Authorized release operator | Prior version restored and health/tenant checks pass | Data incompatibility, failed health checks, uncertain source identity | Timed rollback record and validation results | **MISSING OR UNVERIFIED** |
| Database restore | [`ISOLATED_POSTGRES_RESTORE_DRILL.md`](./ISOLATED_POSTGRES_RESTORE_DRILL.md) | Authorized database/recovery operator | Archive preflight, isolated restore integrity, schema/migration checks, cleanup, and later operational-backup application validation | Backup integrity failure, environment ambiguity, destructive-target risk, failed reconciliation, or uncertain source/backup identity | Restore evidence JSON, retained artifact, timed operational restore record, measured RTO/RPO, and integrity proof | **RUNNABLE MECHANICS / OPERATIONAL EVIDENCE OUTSTANDING** |
| Incident response | No canonical executable runbook linked yet | Incident commander or designated responder | Severity, containment, notification, evidence preservation, closure | Missing authority, unsafe containment step, evidence-loss risk | Incident timeline and decision record | **MISSING OR UNVERIFIED** |
| Secret rotation and revocation | No canonical executable runbook linked yet | Authorized security/cloud administrator | Replacement works, prior credential revoked, audit trail retained | Replacement failure, inability to revoke, service-impact uncertainty | Rotation and revocation evidence | **MISSING OR UNVERIFIED** |
| Failed-rotation recovery | No canonical executable runbook linked yet | Authorized security/cloud administrator | Service restored without reactivating compromised material | Unknown active credential, audit gap, uncontrolled rollback | Recovery record and final credential inventory | **MISSING OR UNVERIFIED** |
| Break-glass access | No canonical executable runbook linked yet | Explicitly authorized emergency operator | Access is time-bound, logged, reviewed, and revoked | Unlogged access, unclear approver, inability to revoke | Approval, access, action, and revocation record | **MISSING OR UNVERIFIED** |
| Monitoring and alert test | No canonical executable runbook linked yet | Authorized operations operator | Alert generated, delivered, acknowledged, and retained | Missing destination, silent failure, unverifiable identity | Alert-test and acknowledgement evidence | **MISSING OR UNVERIFIED** |

## Runbook acceptance standard

Each canonical runbook must identify:

- purpose and scope;
- authorized operator and approver;
- required access, tools, credentials, environment, and source identity;
- effective date, last-reviewed date, and supersession status;
- exact commands or controlled steps;
- validation checks and expected results;
- abort and escalation criteria;
- rollback or recovery path;
- evidence files, timestamps, and retention location;
- relation to the controlling lane issue and immutable release SHA.

A checklist, architecture note, historical evidence packet, workflow definition, or issue comment is not an executable runbook unless it satisfies this standard and is linked from this gateway.

## Consolidation rule

New operational documents belong under `docs/operations/`. Do not add new material to `docs/ops/`.

Existing files under `docs/ops/` must be inventoried before relocation or deletion. Each file must be classified as canonical, supporting, historical, superseded, generated evidence, or obsolete. Preserve Git history and identify replacements when material is superseded.

## Review standard

An authorized reviewer or successor must validate from a clean clone that the operational path is understandable without undocumented assistance. Ownership, credentials, external services, production access, and actual execution evidence remain subject to verified handoff and the controlling eight-lane program.
