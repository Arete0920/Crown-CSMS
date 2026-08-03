# CROWN Current Release Status

**Date:** 2026-08-03  
**Repository:** `tcmegahan/Crown2026`  
**Last reconciled source snapshot:** `6f9bb70b63e099199f460bc0eb90837903a9f3bc`  
**Live identity rule:** resolve the current `main`, immutable release tag, workflow runs, and deployed runtime directly from GitHub and the production endpoints; this document records posture and evidence boundaries, not a self-updating Git ref.  
**Status basis:** exact repository commits, exact-head workflow evidence, deployed runtime evidence, and controlling issue `#1619`

## Canonical decision

CROWN remains under **bounded final remediation before selection of the final immutable release candidate**.

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DEFERRED — NEW OWNER; DISABLED; REQUIRED TO FAIL CLOSED**
- Controlled diligence and explicitly authorized demonstrations: permitted only with accurate disclosures

GitHub issue `#1619` and its eight lane issues are the sole controlling production-readiness and buyer-handoff framework. Repository checks, issue closure, pull-request completion, documentation updates, or partial evidence do not establish production or buyer readiness.

## Verified completed work — do not repeat

- Governed request-serving coverage passed at `77.59659410394408%` against the unchanged 75% requirement.
- Conservative operational-inclusive coverage passed at `77.26145725025994%`.
- The accepted coverage execution completed with `4,319 passed`, `8 skipped`, and zero failures or errors; threshold, exclusions, source boundary, and `.coveragerc` were unchanged.
- The production-surface inventory framework completed with `2,360` mapped surfaces across all `10` required domains, zero validation errors, zero duplicate identifiers, and zero `UNMAPPED` surfaces.
- Production Deploy run `30812926506` successfully deployed backend SHA `e3eeebe461e1ecc626e2855cb680ec4eadc83c7d` with migration, build, scan, deployment, health, and identity checks.
- The deployed frontend and backend both reported SHA `e3eeebe461e1ecc626e2855cb680ec4eadc83c7d` and tag `prod-deploy-20260803-e3eeebe`.
- Exact-parity certification run `30817788322` passed deployment-identity validation and the Heritage passwordless school-administrator session, but failed the browser/runtime campaign. It is failure evidence, not production authorization.
- Passwordless Heritage repository remediation and the supported open-session production configuration are complete. The obsolete invitation-secret path must not be recreated.
- PR `#1866` merged at `ed620e0bdb4a24ad99bf50223d55a93cc785fd88` after exact-head terminal-success evidence. Its full backend run completed with `4,338 passed`, `8 skipped`, `132` subtests passed, and zero failures. The Sandbox evidence gate, tenant-isolation gate, production-surface inventory, route and duplicate checks, builds, security scans, and release gates also passed.
- PR `#1868` merged at `6f9bb70b63e099199f460bc0eb90837903a9f3bc` after exact-head terminal-success evidence. The frontend dependency lock now resolves `brace-expansion` to patched version `5.0.9`; `npm ci`, high-severity `npm audit`, dependency integrity, dependency review, security scans, builds, and the required regression/evidence gates passed.
- Production deployment, rollback, restore, evidence-contract, and release-identity mechanisms exist. Their existence is credited; the remaining operational exercises are not complete.

## Current repository work

- This bounded two-file authority reconciliation is the final planned source change before release freeze.
- No final immutable release candidate has been selected. The currently deployed `e3eeebe...` identity is valid historical deployment evidence but does not include the merged runtime and dependency repairs and cannot be the final release identity.
- Exact release identity must be selected only after this authority reconciliation merges and after the final repository-distribution boundary is verified.

## Remaining completion evidence

The following evidence remains required before production authorization:

1. verify the final current Git-history and distributable-bundle boundary;
2. freeze one final SHA and immutable production tag;
3. deploy backend and frontend from that exact SHA/tag and reconcile migration, build, configuration, and runtime identity;
4. run one exact-parity production certification campaign for required personas, routes, tenant/RBAC denials, provenance, audit attribution, and payment containment;
5. demonstrate monitoring, alert delivery, acknowledgement, escalation, drift detection, and incident response;
6. execute application rollback and isolated database restore using an approved operational backup or accepted substitute, with measured and accepted RTO/RPO;
7. complete the metadata-only inventory and representative lifecycle exercises for active credentials and privileged access, including rotation, failed-rotation recovery, revocation, and controlled break-glass access;
8. verify active vendors, regions, agreements, DPAs, retention, support access, subprocessors, and incident obligations;
9. execute representative synthetic correction, bounded export and denial, deletion or anonymization, legal-hold, and restored-backup handling exercises;
10. reconcile the final evidence package and record separate limited-production, buyer-handoff, and payment decisions.

## Security and repository-distribution boundary

The historical Ed25519 private-key path was:

`solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem`

Accepted evidence records that a rewritten mirror previously removed the forbidden path, passed full repository verification, returned zero all-ref Gitleaks findings, and produced zero findings across reachable DOCX blobs. That proof is historical preparation and must be refreshed against the final authoritative refs and distributable artifacts.

The Founder/Product Owner attested that the exposed Ed25519 key was repository-only and was not installed, registered, trusted, or used in an external production, signing, attestation, Azure, GitHub, Solomon, or other runtime system. Based on that attestation, no external revocation, downstream trust migration, or replacement production key is required solely for this incident unless contrary evidence is discovered.

The remaining boundary is limited to final authoritative-ref verification, exact-path absence, all-ref secret scanning, fresh-clone verification, stale artifact and bundle replacement, and production of a clean distributable diligence bundle.

## Payment-processing boundary

Payment-provider selection, contracting, credentialing, transaction certification, and activation are **DEFERRED — NEW OWNER**. No payment processor is approved for production operation. Card, ACH, autopay, processor webhook, refund, settlement, dispute, and external payment-confirmation paths must remain disabled unless a future owner-authorized processor-specific program implements and certifies them.

Provider-neutral accounting, billing, ledger, invoice, balance, payment-record, and payment-plan source material may be retained for diligence. Its presence does not establish payment-processing readiness.

## Buyer and successor handoff

No buyer, successor, or new owner has been approved for operational turnover. Repository preservation and diligence preparation do not constitute operational transfer, acceptance, or readiness.

## Compliance claim boundary

CROWN may be described only as designed to support schools in meeting applicable student-data privacy and security obligations. It must not be described as FERPA certified, COPPA certified, universally compliant, regulator approved, or compliance guaranteed.

## Repository operation during final remediation

Permitted source changes are limited to:

- this bounded canonical-authority correction;
- a bounded evidence-supported repair only if a final exact-SHA gate proves a new defect;
- final evidence-index, limitations, runbook, and owner-handoff reconciliation before the immutable release freeze.

After the source freeze, permitted work is limited to exact-SHA deployment and certification evidence, execution and recording of the remaining operational lanes, and final decision records that do not alter the frozen release source.

Coverage development, another master plan, another production-surface inventory redesign, passwordless-access reconstruction, deployment-system reconstruction, broad speculative remediation, and payment-provider selection are excluded.

## Current final status

**REPOSITORY STATE: RUNTIME AND DEPENDENCY REPAIRS MERGED; FINAL BOUNDED AUTHORITY RECONCILIATION IN PROGRESS; NO FINAL IMMUTABLE RC SELECTED**  
**PRODUCTION DECISION: NOT APPROVED / NO-GO / HOLD**  
**BUYER TURNOVER: NOT APPROVED**  
**PAYMENT PROCESSING: DISABLED / FAIL CLOSED**  
**PAYMENT OWNERSHIP: DEFERRED — NEW OWNER**  
**HISTORY REMEDIATION: FINAL CURRENT-REF AND DISTRIBUTION VERIFICATION REQUIRED**
