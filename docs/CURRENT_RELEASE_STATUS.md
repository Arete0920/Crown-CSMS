# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last repository security update:** 2026-09-26  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point  
**Release rule:** production-ready status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build, and release gates are passing.

## Current decision

The August 18, 2026 engineering certification remains historical evidence for that certified baseline. Subsequent dependency, scheduling, architecture, and repository-governance changes require exact-head verification before a current production-ready claim is made.

The security dependency update merged on September 26, 2026 and upgrades affected backend and frontend dependencies. Current release readiness must be evaluated on the resulting exact head plus any subsequently merged release-hygiene change.

## Required release gates

A production-ready release requires, as applicable:

1. dependency audit and vulnerability scan PASS;
2. CodeQL/static-analysis PASS;
3. secret scan PASS;
4. backend and frontend test gates PASS;
5. tenant-isolation and authorization gates PASS;
6. schema and migration-governance PASS;
7. build and route certification PASS;
8. repository-policy and release-authority PASS;
9. no unresolved critical or high-severity findings;
10. exact release head recorded in immutable release evidence.

**No successor production tag or release is asserted by this record.**

## Operational boundary

Repository release readiness is separate from environment-specific production operation. Deployment, monitoring ownership, credentials, backups, restore exercises, provider activation, and runtime acceptance must be verified for the selected production environment.

## Payment boundary

**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Provider selection and contracting, merchant credentials, transaction/webhook/settlement/refund/dispute/reconciliation certification, and applicable legal/accounting review remain separate authorization requirements.

## Claim boundary

Until the current exact head passes all applicable release gates, the approved statement is:

> **CROWN has an established production-engineering baseline and is under exact-head release verification following current security and repository-maintenance updates.**

After all applicable gates pass on the exact release head, this record may be updated to identify that head as the current production-ready source baseline.
