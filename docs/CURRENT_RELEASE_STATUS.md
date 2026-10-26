# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last release-governance reconciliation:** 2026-10-25 (dated operational checkpoint below; verify live source separately)  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point  
**Release rule:** production-ready source status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build, repository-policy, and release-authority checks are passing.

## Current decision

The August 18, 2026 engineering certification remains historical evidence for that certified baseline. Subsequent dependency, scheduling, architecture, security, and repository-governance changes require exact-head verification before a current production-ready source claim is made.

Current release authority is defined by this document, the canonical document index, the diligence evidence index, exact-head CI, and current supporting evidence. Dated predecessor-era release campaigns and retired comparison/superiority artifacts remain provenance only and are not executable release authority.

## Latest verified release checkpoint — October 25, 2026 (20:29 Eastern / October 26 UTC)

**Technical/operational certification: NOT YET PASSED.** Current source must always be resolved again from protected `main` at the actual release decision. The protected-main checkpoint reviewed for this record was `4f36a58cde1e22dbd3921883655b59fd226ef4a8`, after guarded integration of PRs #463–#468. Main-branch CI had passing security, tenant, dependency and repository-policy jobs; comprehensive backend coverage and survey PostgreSQL verification were still in progress at the inspection. Do not interpret pending checks as successful.

The following **later evidence supersedes the earlier failed recovery/migration/runtime observations**, without proving current-HEAD Azure acceptance:

- **Actual isolated DEV database recovery succeeded:** [GitHub Actions run 40220289175](https://github.com/Arete0920/Crown-CSMS/actions/runs/40220289175) passed at historical accepted source `1f1489c00b03ec21ad35c136a58b481a49e91cfb`. Issue [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) records a disposable PostgreSQL recovery matching 464 source tables and 241 migration-history rows; temporary resources were removed. This establishes one successful bounded recovery drill, **not** current-head rollback compatibility, retained backup policy, or approved RTO/RPO.
- **Reviewed DEV schema evidence progressed:** [run 40222479744](https://github.com/Arete0920/Crown-CSMS/actions/runs/40222479744) completed the governed CRM + legacy refresh schema staging; [fresh read-only inspection 40223025521](https://github.com/Arete0920/Crown-CSMS/actions/runs/40223025521) passed and reported **zero pending reviewed migrations at that timestamp**. This does not authorize or establish SimpleJWT blacklist activation; the blacklist's actual hosted schema and enabled enforcement remain separate issue [#350](https://github.com/Arete0920/Crown-CSMS/issues/350), as does legacy refresh-client acceptance [#372](https://github.com/Arete0920/Crown-CSMS/issues/372).
- **An earlier exact-source DEV backend deployment succeeded:** [run 40223430678](https://github.com/Arete0920/Crown-CSMS/actions/runs/40223430678) passed for historical SHA `1f1489c00b03ec21ad35c136a58b481a49e91cfb`. The [subsequent read-only preflight 40224098833](https://github.com/Arete0920/Crown-CSMS/actions/runs/40224098833) **failed** because the DEV preview frontend build identity remained stale; its retained receipt reported healthy DEV database/backend identity, API owner anonymous denials, and configured CORS at that older source. Later current-main deployment parity and authenticated walkthroughs are **not verified**.
- **Source safeguards subsequently merged:** [#463](https://github.com/Arete0920/Crown-CSMS/pull/463) rejects redirected frontend build-identity responses; [#464](https://github.com/Arete0920/Crown-CSMS/pull/464) checks exact protected main before preview build and upload; [#465](https://github.com/Arete0920/Crown-CSMS/pull/465) repaired the Playwright runner; [#466](https://github.com/Arete0920/Crown-CSMS/pull/466) retired the emergency HTTP seed route; [#468](https://github.com/Arete0920/Crown-CSMS/pull/468) hardened DEV school-discovery runtime guards; [#467](https://github.com/Arete0920/Crown-CSMS/pull/467) enforces shared authentication rate-limit cache in hosted/hardened runtimes. Each is **source integration only**. Hosted Redis availability and DEV runtime/client acceptance remain unverified.
- **Evidence custody:** [issue #427](https://github.com/Arete0920/Crown-CSMS/issues/427) records five historical, sanitized Actions evidence archives retained in a verified controlled evidence ZIP. The ZIP SHA-256 is `585e9155cd7bfb6a83eb3db37e6fa601ff29b446b4e22fec7809c6abd3a3a820`; all five embedded archives matched the included checksum manifest. **An independently controlled off-platform copy is not yet verified.** Original Actions artifacts have recorded November 1, 2026 retention expiration.

**Outstanding P0 acceptance:** exact-current-main API/frontend SHA parity and read-only runtime precheck [#427](https://github.com/Arete0920/Crown-CSMS/issues/427); authenticated owner console [#414](https://github.com/Arete0920/Crown-CSMS/issues/414); one approved synthetic provisioning exercise [#420](https://github.com/Arete0920/Crown-CSMS/issues/420); canonical own-family/wrong-family/cross-tenant privacy tests on both aliases [#441](https://github.com/Arete0920/Crown-CSMS/issues/441); hosted JWT revocation/replay/client acceptance [#350](https://github.com/Arete0920/Crown-CSMS/issues/350) and [#372](https://github.com/Arete0920/Crown-CSMS/issues/372); effective operations-credential retirement [#269](https://github.com/Arete0920/Crown-CSMS/issues/269); historical signing-key trust/ref remediation [#104](https://github.com/Arete0920/Crown-CSMS/issues/104); and full exact-deployment application certification [#273](https://github.com/Arete0920/Crown-CSMS/issues/273). None is closed by source CI.

**Release disposition:** No real-school production GO, payment activation, or buyer-distribution certification. Preserve existing source-governance and deployment controls. A separately approved operator may perform current-SHA DEV verification; this document grants no Azure, schema, secret, payment, school-data or Git-history mutation authority.

### Superseded earlier checkpoint (provenance only)

The October 25 protected-main checkpoint at `2793a1a516ddad53fdec90d5b238549b94082f7b` identified an unsuccessful [older recovery run 40196714936](https://github.com/Arete0920/Crown-CSMS/actions/runs/40196714936), an older schema inventory reporting four pending migrations ([40185693789](https://github.com/Arete0920/Crown-CSMS/actions/runs/40185693789)), and a stale frontend precheck ([40196784450](https://github.com/Arete0920/Crown-CSMS/actions/runs/40196784450)). Those observations remain historical evidence of their own source/time only. **Do not treat them as the latest DEV state or rerun successful recovery/schema stages solely to reproduce evidence.**

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
