# CROWN Open Issue Execution Matrix

Status date: 2026-07-17
Main SHA at preparation: `cfe46095cd40ba00371c38edf84b1d35ed73e278`

This is the controlling index for remaining work. Issue-specific acceptance criteria still apply. Production is not approved.

## Rules

- One active production-critical implementation lane at a time.
- Completion requires the stated evidence, not code intent or a merged PR alone.
- Runtime, recovery, infrastructure, and operational proof must be performed in the environment they concern.
- Parent trackers remain open until their child evidence is complete.
- Payment processing remains disabled under the Product Owner hold recorded in issue 1298.

## Ordered lanes

1. **Deployed runtime evidence — 1274, 1276, 1287, residual 1351**
   - 1408 added tenant-context runtime proof; 1409 added automatic execution after successful main deployment.
   - Required: exact deployed identities, authenticated route screenshots and network records, console results, tenant-context proof, complete route matrix, and data provenance classification.

2. **Recovery and restore — 1270**
   - Required: controlled failed-deploy or rollback exercise, isolated database restore exercise, actual recovery timing, recovery point, decision tree, and artifacts.

3. **External secrets operations — 1294, 1296**
   - Required: workload identity, external secret-store retrieval, audit evidence, rotation, failed-rotation recovery, and break-glass exercise.

4. **Tenant architecture convergence — 1352**
   - Canonical context exists from `eda6de9c2bef41b833b182357bdf0829d13b7a3e`; whoami migration exists from `197c4f7c2b03454509d6e60a302a349f000588ad`.
   - Required: migrate remaining consumers, explicit override permission, exemption inventory, task cleanup proof, and safe retirement of redundant middleware.

5. **Canonical identity model — 1353**
   - Inventory exists from `26fc753468578c3a23dca6b5350150f835ca38b9`; guardian-household canonical writer exists from `452d37e3aab6e8ed3100690cbbb2f349209186ac`.
   - Required: three-model-set reconciliation, deterministic mapping, representative migration rehearsal, cross-module tests, and rollback proof.

6. **CI proof hierarchy — 1394**
   - Required: classify every workflow as merge gate, advisory, deployment proof, runtime proof, scheduled audit, or obsolete duplicate; remove unnecessary duplicate execution without weakening controls.

7. **Successor operation — 1393**
   - Required: clean-room clone, configure, test, modify, deploy, operate, rollback, and recover exercise using canonical documentation and approved access.

8. **Final documentation and authority — 1277, 1275, 1374**
   - Required after all prior lanes: reconcile release documents, run final same-SHA ceremony, and record Founder/Product Owner authority.

## Current classification

| Issue | State |
|---|---|
| 1270 | recovery evidence required |
| 1274 | authenticated deployed evidence required |
| 1275 | final authority tracker |
| 1276 | deployed visual QA required |
| 1277 | final documentation reconciliation |
| 1287 | deployed tenant-context evidence required |
| 1294 | external secret-store proof required |
| 1296 | secret operations exercises required |
| 1351 | residual transport and runtime proof required |
| 1352 | staged tenant convergence remains |
| 1353 | identity migration and reconciliation remain |
| 1374 | controlling sprint tracker |
| 1393 | clean-room exercise required |
| 1394 | CI rationalization required |

Issue 1298 is closed as not planned for the current release. No payment processor is represented as selected, enabled, certified, or production-ready.
