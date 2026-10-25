# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last release-governance reconciliation:** 2026-10-25 (dated operational checkpoint below; verify live source separately)  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point  
**Release rule:** production-ready source status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build, repository-policy, and release-authority checks are passing.

## Current decision

The August 18, 2026 engineering certification remains historical evidence for that certified baseline. Subsequent dependency, scheduling, architecture, security, and repository-governance changes require exact-head verification before a current production-ready source claim is made.

Current release authority is defined by this document, the canonical document index, the diligence evidence index, exact-head CI, and current supporting evidence. Dated predecessor-era release campaigns and retired comparison/superiority artifacts remain provenance only and are not executable release authority.

## Dated operational checkpoint — October 25, 2026

**Engineering release decision: NO-GO for operational production certification or the November 1 soft launch.** The latest reviewed protected-main SHA at this checkpoint was `2793a1a516ddad53fdec90d5b238549b94082f7b` (after the protected merge of PR #456). This is a dated observation, **not** an instruction to pin later commands to that SHA; resolve `refs/heads/main` again before any run.

- The [hosted read-only DEV precheck](https://github.com/Arete0920/Crown-CSMS/actions/runs/40196784450) did not establish current backend/frontend artifact identity or the required anonymous platform authorization denials. Its deployed build-identities were older than the accepted main at observation time. Browser/API runtime certification is outstanding; do not conflate HTTP 200 health with release readiness.
- The [authorized DEV recovery attempt](https://github.com/Arete0920/Crown-CSMS/actions/runs/40196714936) verified source TLS and read-only snapshot access but **failed at the PostgreSQL export** before restoring to a disposable database. No successful operational backup/restore, accepted RTO/RPO or rollback-image compatibility is asserted.
- A corrected disposable-client CA prerequisite passed [generated-fixture and recovery-contract verification](https://github.com/Arete0920/Crown-CSMS/actions/runs/40198088496) on its recorded branch SHA. This is not operational DEV restore proof or acceptance on a successor protected main.
- The [earlier DEV schema inventory](https://github.com/Arete0920/Crown-CSMS/actions/runs/40185693789) identified four pending migrations. Their current status requires a fresh, governed, read-only plan before any separately authorized staging.
- Security/operations acceptance records remain open, including [DEV recovery/runtime #427](https://github.com/Arete0920/Crown-CSMS/issues/427), [credential retirement #269](https://github.com/Arete0920/Crown-CSMS/issues/269), and [historic signing key #104](https://github.com/Arete0920/Crown-CSMS/issues/104). A source merge or passing CI does not itself close these operational requirements.

This checkpoint records historical verified findings without modifying release gates, granting permission to deploy, staging migrations, accessing school records, activating payments, or asserting certification. Supersede it only with newer retained, exact-source operational evidence.

## Required repository release gates

A production-ready source release requires, as applicable:

1. dependency audit and vulnerability scan PASS;
2. CodeQL/static-analysis PASS;
3. secret scan PASS;
4. backend and frontend test gates PASS;
5. tenant-isolation and authorization gates PASS;
6. schema and migration-governance PASS;
7. build and route certification PASS;
8. repository-policy and release-authority policy PASS;
9. no unresolved critical or high-severity repository findings;
10. exact release head recorded in immutable release evidence.

The protected `Release authority gates` status is a repository/source-governance control. It must validate the current authority hierarchy and must not automatically convert missing environment-specific runtime evidence into a source-code merge failure.

## Operational production certification

Environment-specific production certification is a separate, explicit fail-closed activity. It must be intentionally invoked for a selected deployment and exact SHA and must not be inferred from repository CI.

Operational certification may require current evidence for deployed identity, dashboard/runtime provenance, migration rehearsal and reconciliation, financial runtime controls, performance/load behavior, monitoring and incident readiness, rollback/restore exercises, credentials, provider activation, and final operational acceptance.

A missing or failed operational-certification artifact blocks the corresponding operational claim. It does not retroactively invalidate otherwise passing repository/source engineering evidence.

**No successor production tag or release is asserted by this record.**  
No successor production deployment, runtime identity, or operational acceptance is asserted by this record.

## Payment boundary

**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Provider selection and contracting, merchant credentials, transaction/webhook/settlement/refund/dispute/reconciliation certification, and applicable legal/accounting review remain separate authorization requirements.

## Claim boundary

Until the current exact head passes all applicable repository release gates, the approved statement is:

> **CROWN has an established production-engineering baseline and is under exact-head release verification following current security and repository-maintenance updates.**

After all applicable repository gates pass on the exact release head, the source baseline may be identified as current production-ready engineering. Environment-specific deployment and operational acceptance remain separate evidence-backed decisions.
