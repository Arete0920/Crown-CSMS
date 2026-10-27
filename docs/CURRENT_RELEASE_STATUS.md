# CROWN Current Release Status

**Status:** RELEASE CANDIDATE — EXACT-HEAD VERIFICATION REQUIRED  
**Last release-governance reconciliation:** 2026-10-27 (dated DEV checkpoint below; resolve live source at the next decision)  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point  
**Release rule:** production-ready source status is granted only to an exact repository head whose applicable security, dependency, test, schema, tenant-isolation, build, repository-policy, and release-authority checks are passing.

## Current decision

The August 18, 2026 engineering certification remains historical evidence for that certified baseline. Subsequent dependency, scheduling, architecture, security, and repository-governance changes require exact-head verification before a current production-ready source claim is made.

Current release authority is defined by this document, the canonical document index, the diligence evidence index, exact-head CI, and current supporting evidence. Dated predecessor-era release campaigns and retired comparison/superiority artifacts remain provenance only and are not executable release authority.

## October 27, 2026 — latest verified Azure DEV release checkpoint

**Accepted protected source at verification:** `d8bb1af7f62bbada8ede2146f0dd92964fbe7157` from `refs/heads/main`. **Azure DEV deployment identity: VERIFIED; full operational and production certification: NOT VERIFIED.** This is a timestamped observation, not perpetual proof of the deployed state.

- **Backend source and runtime:** [DEV deploy 40488869833](https://github.com/Arete0920/Crown-CSMS/actions/runs/40488869833) completed SUCCESS. During rollout the live build initially showed an earlier SHA, then converged to the exact protected source. API health HTTP 200 and DEV database READY were observed later in the independent read-only monitor.
- **Frontend source and runtime:** [isolated SWA DEV preview deploy 40490150394](https://github.com/Arete0920/Crown-CSMS/actions/runs/40490150394) completed SUCCESS with an exact-SHA build identity check. Deployment-only inputs deliberately **skipped** Playwright/browser certification, buyer persistence, synthetic tenant setup, two-tenant tests and production certification. Those steps must not be reported as passed.
- **Independent exact-SHA parity evidence:** [Repository Freshness 40503102959](https://github.com/Arete0920/Crown-CSMS/actions/runs/40503102959), sanitized artifact **12733956813**, captured **2026-10-27 12:21:30 UTC**; original ZIP integrity/CRC PASS, SHA-256 `670c3fd11c6dea18063ce37dbc2963d56fd10657ac85c8c018b231f97f59b9f6`. Its `precheck=PASS` establishes observed backend build SHA, packaged backend artifact SHA and DEV preview build SHA **all equal** to the protected main SHA; API HTTP 200, DEV/DB READY, tested anonymous owner requests DENIED, and preview CORS READY. It explicitly records authenticated owner acceptance `NOT_TESTED`, provisioning `NOT_TESTED`, and overall certification `NOT_VERIFIED`. **The older frontend/backend version-drift finding is superseded** by this later successful same-SHA evidence; no redeployment solely for parity is indicated.
- **Azure Managed Redis control plane:** [Azure Classroom Release Preflight 40482237271](https://github.com/Arete0920/Crown-CSMS/actions/runs/40482237271), artifact **12723880471**, captured **09:38:51 UTC**, ZIP CRC PASS, SHA-256 `5f1efebc00d674b9ab4c2a86fbf2c61d8272ae593024f40be6adb52515f8581c`. Existing resource, Balanced B0 database, App Service VNet, private endpoint and DNS configuration metadata report **CONSISTENT**. The names of app settings and DNS A records are **PRESENT_ONLY**. Effective Key Vault/secret resolution, App Service subnet DNS, live Redis/TLS connectivity, cross-worker throttling HTTP 429 and cache-unavailable HTTP 503 are **NOT TESTED**. Do not re-provision the existing resource without a separate concrete finding.
- **Read-only DEV schema:** [blacklist inventory 40482329479](https://github.com/Arete0920/Crown-CSMS/actions/runs/40482329479), artifact **12723532175**, captured **09:39:20 UTC**, ZIP CRC PASS, SHA-256 `09f19713d39dc5ce879a36c48fcf115f675b88ced8f8c6e887bb528311a9f6e6`. Target verified, read-only transaction and DB TLS verified; SimpleJWT blacklist classified **CLEAN_UNINITIALIZED**, both blacklist tables absent, no vendor blacklist migration records, activation **NOT AUTHORIZED**. The companion reviewed CRM/legacy-refresh migration inspection logged **zero pending reviewed migrations**; this does not certify active one-use refresh behavior, blacklist tables, or SimpleJWT runtime version. The separately gated blacklist migration stage was **SKIPPED**.
- **Exact-head engineering gates:** [Tests 40446855431](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855431), [CodeQL 40446855277](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855277), [secret-scan 40446855476](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855476), [Schema Governance 40446855577](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855577) and [Release Authority 40446855317](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855317) succeeded at that source. The earlier same-SHA [Repository Freshness 40446855242](https://github.com/Arete0920/Crown-CSMS/actions/runs/40446855242) **failed while DEV was still stale**; it is preserved, not erased or reclassified by the later successful runtime monitor. Production operational certification was deliberately skipped.

**Unresolved launch and security gates:** hosted exact-SHA authenticated crawler/registrar/parent/administrator/tenant journeys [#273](https://github.com/Arete0920/Crown-CSMS/issues/273); real owner-console access [#414](https://github.com/Arete0920/Crown-CSMS/issues/414); authorized synthetic provisioning [#420](https://github.com/Arete0920/Crown-CSMS/issues/420); own-family/wrong-family and cross-tenant privacy [#441](https://github.com/Arete0920/Crown-CSMS/issues/441); live Redis enforcement and selected-target recovery/rollback [#427](https://github.com/Arete0920/Crown-CSMS/issues/427); controlled SimpleJWT schema installation/activation [#350](https://github.com/Arete0920/Crown-CSMS/issues/350) and legacy refresh replay/client acceptance [#372](https://github.com/Arete0920/Crown-CSMS/issues/372); effective DEV reset credential retirement [#269](https://github.com/Arete0920/Crown-CSMS/issues/269); historical Ed25519 key trust and reachable-history disposition [#104](https://github.com/Arete0920/Crown-CSMS/issues/104). Azure migration of the separate Arete/Jireh/portfolio websites remains distinct under [#429](https://github.com/Arete0920/Crown-CSMS/issues/429) and [#440](https://github.com/Arete0920/Crown-CSMS/issues/440).

**October 29 technical-certification objective:** still **OPEN** pending acceptance evidence. **November 1 unrestricted production, real-school and payment activation:** **NO-GO** pending explicit operational and provider acceptance. This status update grants no migration, feature-flag, secret, Azure deployment, production, real-school, shared-Git-history or payment authorization.

### October 27, 2026 — verified historical evidence custody

**Independent off-platform preservation: VERIFIED for 31 identified original archives.** The [custody receipt](https://github.com/Arete0920/Crown-CSMS/issues/427#issuecomment-6455126087) records preservation of historical evidence; it grants no current operational or production certification.

- **Package:** `CROWN_Historical_Certification_Evidence_2026-10-27.zip`, **98,356 bytes**, SHA-256 `4ca3fc8aa82f13ceb01e1a5ee28cf45f418f73e1f2b9fbd5825553a41e937de0`. The private `CROWN_Preservation_Receipt_2026-10-27.json` has SHA-256 `c54b0417499b02b8bb1b1a45bb897d2c9f4806b07a4e5e26db9cbe2a4d1f38ea`; storage locators remain in that controlled receipt.
- **Coverage and reuse:** 30 operational originals and one existing source-test original; nine distinct originals reused from freshly verified copies and 22 newly downloaded. Overlapping originals in the earlier packages were deduplicated; each original appears once. All **16 identified CROWN operational originals expiring before November 2 UTC** are included, including 11 without a verified prior copy in the inspected collection. The earliest included expiration is **October 30, 2026, 19:27:21 UTC**, artifact `12527270038` / run `40011310836`. Artifact `12596130968` / [run 40185019025](https://github.com/Arete0920/Crown-CSMS/actions/runs/40185019025), expiring **November 1, 10:30:20 UTC**, is also preserved.
- **Verified custody:** owner-controlled Microsoft OneDrive upload at **21:48:45 UTC**, fresh retrieval at **21:49:09 UTC**, byte-for-byte match; all 31 embedded originals match GitHub SHA-256/size metadata and pass ZIP CRC. One owner permission and no public-link scope were observed. A separate controlled project copy passed fresh byte-for-byte retrieval at **21:49:45 UTC**. The manifest retains full source run/artifact IDs, commit SHAs, capture/creation/expiration timestamps, member hashes and prior-copy references.
- **Bounded result:** 41 artifact metadata records inventoried; 10 companion records explicitly excluded from the package. Nine inspected runs returned no artifact ZIPs, and raw job logs were not preserved. Prior migration-plan statements and earlier workflow-attempt evidence retain their documented provenance limits. No immutable retention policy, current deployment acceptance, recovery/rollback certification or release authorization is established. Issue [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) remains OPEN for its operational criteria.

### Historical checkpoint — October 25, 2026 (20:29 Eastern / October 26 UTC)

**Technical/operational certification: NOT YET PASSED.** Current source must always be resolved again from protected `main` at the actual release decision. The protected-main checkpoint reviewed for this record was `4f36a58cde1e22dbd3921883655b59fd226ef4a8`, after guarded integration of PRs #463–#468. Main-branch CI had passing security, tenant, dependency and repository-policy jobs; comprehensive backend coverage and survey PostgreSQL verification were still in progress at the inspection. Do not interpret pending checks as successful.

The following **later evidence supersedes the earlier failed recovery/migration/runtime observations**, without proving current-HEAD Azure acceptance:

- **Actual isolated DEV database recovery succeeded:** [GitHub Actions run 40220289175](https://github.com/Arete0920/Crown-CSMS/actions/runs/40220289175) passed at historical accepted source `1f1489c00b03ec21ad35c136a58b481a49e91cfb`. Issue [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) records a disposable PostgreSQL recovery matching 464 source tables and 241 migration-history rows; temporary resources were removed. This establishes one successful bounded recovery drill, **not** current-head rollback compatibility, retained backup policy, or approved RTO/RPO.
- **Reviewed DEV schema evidence progressed:** [run 40222479744](https://github.com/Arete0920/Crown-CSMS/actions/runs/40222479744) completed the governed CRM + legacy refresh schema staging; [fresh read-only inspection 40223025521](https://github.com/Arete0920/Crown-CSMS/actions/runs/40223025521) passed and reported **zero pending reviewed migrations at that timestamp**. This does not authorize or establish SimpleJWT blacklist activation; the blacklist's actual hosted schema and enabled enforcement remain separate issue [#350](https://github.com/Arete0920/Crown-CSMS/issues/350), as does legacy refresh-client acceptance [#372](https://github.com/Arete0920/Crown-CSMS/issues/372).
- **An earlier exact-source DEV backend deployment succeeded:** [run 40223430678](https://github.com/Arete0920/Crown-CSMS/actions/runs/40223430678) passed for historical SHA `1f1489c00b03ec21ad35c136a58b481a49e91cfb`. The [subsequent read-only preflight 40224098833](https://github.com/Arete0920/Crown-CSMS/actions/runs/40224098833) **failed** because the DEV preview frontend build identity remained stale; its retained receipt reported healthy DEV database/backend identity, API owner anonymous denials, and configured CORS at that older source. Later current-main deployment parity and authenticated walkthroughs are **not verified**.
- **Source safeguards subsequently merged:** [#463](https://github.com/Arete0920/Crown-CSMS/pull/463) rejects redirected frontend build-identity responses; [#464](https://github.com/Arete0920/Crown-CSMS/pull/464) checks exact protected main before preview build and upload; [#465](https://github.com/Arete0920/Crown-CSMS/pull/465) repaired the Playwright runner; [#466](https://github.com/Arete0920/Crown-CSMS/pull/466) retired the emergency HTTP seed route; [#468](https://github.com/Arete0920/Crown-CSMS/pull/468) hardened DEV school-discovery runtime guards; [#467](https://github.com/Arete0920/Crown-CSMS/pull/467) enforces shared authentication rate-limit cache in hosted/hardened runtimes. Each is **source integration only**. Hosted Redis availability and DEV runtime/client acceptance remain unverified.
- **Evidence custody:** [issue #427](https://github.com/Arete0920/Crown-CSMS/issues/427) records five historical, sanitized Actions evidence archives retained in a verified controlled evidence ZIP. The ZIP SHA-256 is `585e9155cd7bfb6a83eb3db37e6fa601ff29b446b4e22fec7809c6abd3a3a820`; all five embedded archives matched the included checksum manifest. At that historical checkpoint, an independently controlled off-platform copy had not yet been verified; the October 27 custody record above supersedes that preservation gap for the 31 packaged originals. These original Actions artifacts have recorded November 1, 2026 retention expiration.

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
