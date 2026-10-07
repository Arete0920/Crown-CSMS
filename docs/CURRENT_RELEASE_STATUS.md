# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last release-governance reconciliation:** 2026-10-07  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point  
**Release rule:** production-ready source status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build, repository-policy, and release-authority checks are passing.

## Current decision

The August 18, 2026 engineering certification remains historical evidence for that certified baseline. Subsequent dependency, scheduling, architecture, security, and repository-governance changes require exact-head verification before a current production-ready source claim is made.

Current release authority is defined by this document, the canonical document index, the diligence evidence index, exact-head CI, and current supporting evidence. Dated predecessor-era release campaigns and retired comparison/superiority artifacts remain provenance only and are not executable release authority.

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
