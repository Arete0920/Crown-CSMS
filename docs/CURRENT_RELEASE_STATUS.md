# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last verified repository state:** 2026-10-05  
**Reviewed main SHA:** `5a5b15ea01542710690433645a92a6b4f43e59c2`  
**Release rule:** production-ready status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build and release gates are passing.

## Current decision

CROWN has an established engineering baseline, but current production-ready status is not asserted merely from historical green runs or prior certifications.

The currently reviewed `main` is the authoritative integration line at the decision point. Subsequent cleanup, security, feature or dependency changes must be evaluated on their own exact heads and then on the resulting merged `main`.

Historical certifications remain evidence for the SHA they certified. They do not automatically certify later source.

## Verified repository governance

- `main` is protected.
- Required status checks are enforced for everyone.
- The current protection record contains 16 required contexts, including code analysis, release authority, contract, backend, dependency, secret-scan, schema, pytest, release-verification and repository-policy controls.
- Ordinary pull requests are subject to repository hygiene limits and exact-head verification.
- Historical or superseded PRs and workflow runs are not release authority.

## Required release gates

A production-ready source baseline requires, as applicable:

1. dependency and vulnerability audit PASS;
2. CodeQL/static-analysis PASS;
3. secret scan PASS;
4. backend and frontend test gates PASS;
5. tenant-isolation and authorization gates PASS;
6. schema and migration-governance PASS;
7. build and route certification PASS;
8. repository-policy and release-authority PASS;
9. no unresolved critical or high-severity findings applicable to the release;
10. exact release head recorded in release evidence.

**No successor production tag or hosted production release is asserted by this record.**

## Operational boundary

Repository release readiness is separate from environment-specific production operation. Deployment, monitoring ownership, credentials, backups, restore exercises, provider activation and runtime acceptance must be verified for the selected production environment.

## Payment boundary

**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Provider selection and contracting, merchant credentials, transaction/webhook/settlement/refund/dispute/reconciliation certification and applicable legal/accounting review remain separate authorization requirements.

## AI boundary

Curated Solomon guidance is part of the product baseline. External generative AI remains disabled until its provider gateway is refreshed against current `main`, provider/account controls are configured, contractual and data-control requirements are verified, live synthetic evaluation passes and deployed production certification is completed.

No AI release claim should imply access to student, parent, financial, health, discipline or pastoral records unless a future approved architecture explicitly changes that boundary.

## Claim boundary

Until the selected exact head passes all applicable release gates, the approved statement is:

> **CROWN has an established production-engineering baseline and is under exact-head release verification following current security, feature and repository-maintenance updates.**

After all applicable gates pass on the exact release head, this record may be updated to identify that head as the current production-ready source baseline.
