# CROWN SOC 2 — October 23, 2026 Evidence and Claims Reconciliation

**Status:** INTERNAL MANAGEMENT REVIEW / NOT AN ATTESTATION / POLICY ADOPTION OPEN
**Reconciliation date:** 2026-10-23
**Repository checkpoint inspected:** `b12ed66bc55f5159d044e2ed4c3044ee31b17a5d`
**Related control issue:** [#173](https://github.com/Arete0920/Crown-CSMS/issues/173)
**Release authority:** [CURRENT_RELEASE_STATUS](../CURRENT_RELEASE_STATUS.md)
**Owner:** Proposed Founder / Product Owner; formal per-control appointments remain pending.

## 1. Purpose and authority

This reconciliation is an internal cross-document correction. It does not approve scope, policies, risk scores, recovery objectives or a new deployment; it is not SOC 2 Type I/II assurance. Preserve the October 8 documents as **historical source-specific checkpoints**. Their CI pass counts, risk scores and hosting/planning statements must never silently become current observations. The [SOC 2 readiness plan](SOC2_READINESS_PLAN.md) remains the program authority, and this document records subsequent evidence status and buyer-facing claim constraints.

Use the AICPA Trust Services Criteria (2017 with 2022 revised points of focus) for the eventual criterion-by-criterion matrix and CPA-reviewed scope. The 22 S01-S22 workstreams are internal evidence areas, **not a one-to-one set of AICPA criteria**. Initial proposed category: Security; additional categories require customer-commitment review and CPA scoping. Type I design/implementation as of a date is distinct from Type II operating effectiveness over a period.

**Disposition:** No independent SOC 2 report, auditor fieldwork schedule, independent readiness assessment, management-signed scope or adopted risk register was verified by this reconciliation.

## 2. Evidence-hierarchy and reference control

| Level | Acceptable evidence | Limitation |
| --- | --- | --- |
| D — Documented | Versioned procedures, models, proposed controls | Not adopted or operational |
| A — Approved | Dated management signature, effective version, owner and delegate | Does not itself prove operation |
| S — Source implemented/tested | Exact commit and actual CI logs/test objective, exceptions and scope | Not Azure runtime or repeated operation |
| R — Runtime verified | Authenticated target configuration, deployed SHA, negative controls, timestamped proof | Single observation is not an operating period |
| O — Operating | Population, recurring review records, exceptions/closure over cadence | Not a CPA examination |
| E — External | Independent readiness findings or actual issued CPA report | Scope, period and opinion govern any claim |

No inference between levels. Retain private evidence references, hashes, collectors, reviewers, time zones, exact environments, population and retests; do **not** upload student records, secrets, private contracts or sensitive Azure exports to this public repository.

## 3. Reconciled October 23 source and runtime information

- **October 8 historical baseline:** source `a091504ec4ce37c84037b51e15d9f909fcaf6f91`; 11 returned Actions workflows succeeded; Tests recorded 5,186 passed and 19 skipped, with separate subtest/fixture counts. These observations apply to that source SHA only.
- **October 18 bounded backup rehearsal:** [isolated PostgreSQL fixture restore](https://github.com/Arete0920/Crown-CSMS/actions/runs/39165456638) completed and is linked with the artifact identity in [#173](https://github.com/Arete0920/Crown-CSMS/issues/173). Its 4.121-second generated-fixture restore is **not** a real Azure operational backup, a measured service-level RTO/RPO, or a full recovery/rollback test.
- **October 22–23 source-only authentication progress:** [PR #406](https://github.com/Arete0920/Crown-CSMS/pull/406) and [PR #407](https://github.com/Arete0920/Crown-CSMS/pull/407) merged guarded, explicitly invoked DEV migration preparation. Neither applies target schema, activates token revocation, rotates secrets or certifies deployed authentication. [#350](https://github.com/Arete0920/Crown-CSMS/issues/350) and [#372](https://github.com/Arete0920/Crown-CSMS/issues/372) remain OPEN.
- **Azure boundary:** Publicly observed Azure frontend/API and DEV database investigations exist in [#273](https://github.com/Arete0920/Crown-CSMS/issues/273), but the October 8 blanket 'undeployed' statement is stale as a claim about all environments. Reachability, historical build SHA and health checks do not establish production certification, complete current asset inventory, data locations, configured access/MFA, or exact current main deployed. Require authenticated Azure operator evidence for H01–H07 before final system description.
- **Payment boundary:** CompuWerx is the owner-designated intended gateway; Metro Payment Technologies is a **superseded historical planning lead**. See [CompuWerx vendor requirements](../vendor-coordination/compuwerx.md) and the reconciled [subprocessor register](SUBPROCESSOR_REGISTER.md). No executed processor contract, certified signed webhook or live payment authorization was verified. Payments stay DISABLED / FAIL CLOSED.
- **Outstanding security operations:** [#104](https://github.com/Arete0920/Crown-CSMS/issues/104) historical Ed25519 retirement/history/distributables and [#269](https://github.com/Arete0920/Crown-CSMS/issues/269) DEV operations credential rotation lack required owner/operator receipts. Source fixes are not retirement. Do not distribute affected buyer bundles until the precise issue #104 acceptance requirements are satisfied.
- **Fictional dashboard caveat:** Heritage compliance dashboard training data must not imply CROWN has 86 passing audited controls, approved policies, confirmed auditors or scheduled Type II fieldwork. Templates are fictitious school scenarios, not CROWN SOC 2 operating records. The accompanying demonstration template and regression test address this specific source-level claim risk.

These are bounded source/issue/document observations, not a live inspection of private Azure settings, executed contracts, HR evidence, auditor engagement letters or restricted SOC 2 evidence storage.

## 4. S01–S22 control reconciliation

| Controls | Design/source position | Missing verification / closure owner |
| --- | --- | --- |
| S01–S05 Governance, system description, risk, oversight and policy | Documented drafts; October 8 risk treatment planning | Management-signed service scope, roles/deputies, approved risk scores/treatments, monthly deficiency review, approved policy versions (Founder) |
| S06–S10 Inventory, access, tenant support, provider/device and secrets | Tenant/RBAC source safeguards; architecture/security policies | Live Azure/SaaS/workforce/device populations, MFA/access reviews, denied-role/tenant/support checks, encryption/rotation receipts, #104 and #269 (Operations) |
| S11 Vulnerability management | Source CodeQL, dependency, secret-scan and release gates | Current exact-head required workflows, deployed asset coverage, SLAs, exception register and retest traceability (Operations) |
| S12–S14 Monitoring, incident and recovery | Draft procedures; bounded generated-fixture restore | Full log/alert inventory and delivered alert response, live contact/notification tabletop, selected-environment backup failure test and measured isolated recovery (Operations/Management) |
| S15 Changes and releases | Protected source governance and CI records | Actual production deployment SHA, approved release identity, migration, rollout and rollback evidence for selected environment (Operations) |
| S16 Vendor oversight | Candidate/source-control and planned payment registers | Active vendor/subprocessor population, legal roles, data regions, signed DPA/contract, provider assurance and annual review (Privacy/Legal) |
| S17–S19 Workforce, privacy and retention | Policy and DPA templates; guarded source retention operations | Signed acknowledgments/training, executed customer notices/terms, student-data applicability, requests/deletion/legal holds/backups replay (Owner/Privacy) |
| S20–S22 Independent review / Type I / Type II | Requirements documented | Qualified independent readiness reviewer, findings/closure, CPA engagement and actual report; Type II requires recurring evidence across agreed period (External) |

No current control-level closure percentage is asserted, and **none of the 22 areas is promoted to OPERATING or EXTERNAL merely by this documentation correction**.

## 5. Decision register — management and external dependencies

| Priority | Decision / work | Required signed or independently verifiable outcome |
| --- | --- | --- |
| P0 | Remediate #104 and #269 before affected code/history or access handoff | Secret retirement and clean distributable receipts; never place secret values in public records |
| P0 | Remove unsupported compliance claims from buyer/demo material | Fictional display visibly labeled; current buyer disclosure accurately states report status |
| P0 | Azure H01–H07 authenticated inventory and deployment boundary | Scoped asset/account inventory, locations, production/DEV labels, deploy identity and custody; no automatic cloud mutation |
| P1 | Approve legal organization, proposed CROWN boundary and Diadem/shared-service rationale | Named management approver, effective date, customer commitments and data flows |
| P1 | Approve S01–S19 actual owner/deputy roster, evidence repository, security policies and risk treatment | Dated decisions, conflicts/compensating reviews, policies/targets and due dates |
| P1 | Verify operational access, monitoring, notification, recovery and vendor evidence | Authenticated/sanitized logs, population, successful tests, exceptions and retest |
| P1 | Review student/parent privacy contracts, consent, retention and state overlays | Qualified legal review, approved applicable terms and real workflow evidence |
| External | Readiness review and CPA examination | Engagement/scope/date, actual findings, Type I report, followed by Type II operating evidence and report if pursued |

**Solo maintainer:** The owner may perform engineering tasks but cannot claim independent review of their own sensitive actions. Record conflict, compensating controls and subsequent qualified review. CI is not human approval.

## 6. Buyer-safe disclosure

> Arete Advisory Group has developed documented CROWN security and student-data privacy controls and has implemented multiple repository-level safeguards supported by dated automated tests. SOC 2 preparation and operating-evidence collection remain in progress. Current scope, policies, operating controls and independent assurance require further validation. No independently issued CROWN SOC 2 Type I or Type II report was verified in this review, and none is represented. External payment processing remains disabled pending separate vendor and operational acceptance.

**Handoff rule:** Prepare restricted evidence indexes and sanitized disclosures, not a public dump of sensitive source history, credentials, student data or provider contracts. Buyer access to affected distributables is held by issue #104 until acceptance. This reconciliation does not clear any production or buyer-distribution blocker.

## 7. Validation and closure

- Source-document consistency: historical October 8 records retained as dated evidence and linked to this reconciliation.
- Demo language: unsupported CROWN SOC 2 exam / control pass claims replaced with explicit fictional school content; associated source regression test added.
- All repository changes require a governed exact-head PR, required security/tenant/frontend tests, branch protections, and an accepted protected-main merge. This document itself is **not** proof of those checks passing.
- After merge, verify the final main paths, update issue #173 with that source-only scope, and keep operating and external-assurance checkboxes open.

## 8. October 28, 2026 — operational evidence intake / S01–S22 (proposed, unapproved)

**Inspection baseline:** The review began with accepted protected `main=c6caa580fc0113ec12f99a301f9c7980bf17055b` (39 terminal check-runs: 35 successful, 3 skipped, 1 failed strict DEV public-runtime parity). Subsequently, [security PR #504](https://github.com/Arete0920/Crown-CSMS/pull/504) merged, advancing `main` to `0093b07dd37cd494d46b83fc83cb563217dda936`; its newly triggered check population was **not yet terminal** at inspection. Never transfer the earlier exact-head checks to the newer source or to this documentation PR. [Current release decision](../CURRENT_RELEASE_STATUS.md) and [operational issue #427](https://github.com/Arete0920/Crown-CSMS/issues/427) remain the release/hosting authority.

**Method / evidence custody:** Read the existing plan, reconciliation, security/incident/support/recovery policy drafts, privacy and asset matrices, exact GitHub issue/PR records, and GitHub's check-run API for the above SHAs. GitHub check results and merge state were retrieved directly in this review; prior Azure CLI readbacks, artifact integrity receipts and human operational observations are **referenced from dated issue records**, not independently regenerated or rehashed here. No authenticated Azure control-plane inspection, private access/MFA export, contractual/HR audit, or CPA report was available to this review. No workflow was dispatched and no live school, secret, backup or Azure resource was changed.

**Stage legend:** **D** documented design; **A** management-approved procedure; **S** implemented/tested source or bounded technical exercise; **R** deployed runtime/selected-environment proof; **O** actual recurring operating evidence at the approved cadence; **E** independent assurance. `—` means **not evidenced in inspected material**, not proven absent or failed. `Scoped source`, `historical DEV`, `limited`, and `CI restore` mean **partial evidence only**, not full criterion closure. All `A`, `O` and `E` columns remain `—`; no control is closed. For S20–S22, `D=Plan` only means the assessment/report requirement is described.

### 8.1 Six-stage per-control register

| Control | D | A | S | R | O | E | Evidence anchors / limitations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 Governance and accountability | Draft | — | — | — | — | — | [plan](SOC2_READINESS_PLAN.md), [policy](SECURITY_OPERATING_POLICY.md) |
| S02 System description and communications | Draft | — | — | — | — | — | [scope draft](SOC2_SCOPE_DECISION_20261008.md), [release status](../CURRENT_RELEASE_STATUS.md) |
| S03 Risk assessment and treatment | Draft | — | — | — | — | — | [historical risk draft](SOC2_RISK_ASSESSMENT_20261008.md), [#173](https://github.com/Arete0920/Crown-CSMS/issues/173) |
| S04 Deficiencies and corrective action | Draft | — | — | — | — | — | [#173](https://github.com/Arete0920/Crown-CSMS/issues/173), [reconciliation](SOC2_RECONCILIATION_20261023.md) |
| S05 Policy adoption and exceptions | Draft | — | — | — | — | — | [security](SECURITY_OPERATING_POLICY.md), [incident](INCIDENT_RESPONSE_POLICY.md), [recovery](BACKUP_RESTORE_POLICY.md) |
| S06 Asset, data and workforce inventory | Draft | — | — | — | — | — | [regulated-data inventory](REGULATED_DATA_INVENTORY.md), [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) |
| S07 Identity, MFA and access lifecycle | Draft | — | Scoped source | — | — | — | [source gate #158](https://github.com/Arete0920/Crown-CSMS/pull/158), [support policy](SUPPORT_ACCESS_POLICY.md) |
| S08 Tenant and support isolation | Draft | — | Scoped source | Bounded historical DEV | — | — | [support source #425](https://github.com/Arete0920/Crown-CSMS/pull/425), [DEV run 40593165189](https://github.com/Arete0920/Crown-CSMS/actions/runs/40593165189), [#273](https://github.com/Arete0920/Crown-CSMS/issues/273) |
| S09 Physical/device and provider safeguards | Draft | — | — | — | — | — | [security policy](SECURITY_OPERATING_POLICY.md), [vendor register](SUBPROCESSOR_REGISTER.md) |
| S10 Encryption and secret/key lifecycle | Draft | — | Scoped source | Limited DEV credential path | — | — | [#269](https://github.com/Arete0920/Crown-CSMS/issues/269), [#104](https://github.com/Arete0920/Crown-CSMS/issues/104), [merged #504](https://github.com/Arete0920/Crown-CSMS/pull/504) |
| S11 Vulnerability and patch management | Draft | — | Scoped source | — | — | — | [39 exact-head checks at c6caa580](https://github.com/Arete0920/Crown-CSMS/commit/c6caa580fc0113ec12f99a301f9c7980bf17055b/checks), [DevSecOps](../security/DEVSECOPS_MATURITY_ASSESSMENT_20261009.md) |
| S12 Security logs and alert response | Draft | — | Scoped source | — | — | — | [support audit tests #425](https://github.com/Arete0920/Crown-CSMS/pull/425), [Sentry #504](https://github.com/Arete0920/Crown-CSMS/pull/504) |
| S13 Incident response and notification | Draft | — | Scoped source | — | — | — | [incident procedure](INCIDENT_RESPONSE_POLICY.md), [merged classification #239](https://github.com/Arete0920/Crown-CSMS/pull/239) |
| S14 Backups, PITR and recovery | Draft | — | CI restore demonstrated | — for Azure managed PITR | — | — | [actual DEV snapshot isolated-DB run 40584270959](https://github.com/Arete0920/Crown-CSMS/actions/runs/40584270959), [#427 managed PITR failures](https://github.com/Arete0920/Crown-CSMS/issues/427), [recovery policy](BACKUP_RESTORE_POLICY.md) |
| S15 Change control and deployed identity | Draft | — | Scoped source | Historical DEV, current drift | — | — | [main checks c6caa580](https://github.com/Arete0920/Crown-CSMS/commit/c6caa580fc0113ec12f99a301f9c7980bf17055b/checks), [hosted run 40593165189](https://github.com/Arete0920/Crown-CSMS/actions/runs/40593165189), [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) |
| S16 Vendors and subprocessors | Draft | — | — | — | — | — | [candidate register](SUBPROCESSOR_REGISTER.md), [#505](https://github.com/Arete0920/Crown-CSMS/issues/505) |
| S17 Workforce training and confidentiality | Draft | — | — | — | — | — | [security policy](SECURITY_OPERATING_POLICY.md), [#173](https://github.com/Arete0920/Crown-CSMS/issues/173) |
| S18 Privacy, notices and consent | Draft | — | Scoped source | — | — | — | [privacy matrix](PRIVACY_LEGAL_RECONCILIATION_MATRIX.md), [COPPA](COPPA_POSITION.md), [FERPA](FERPA_POSITION.md), [#441](https://github.com/Arete0920/Crown-CSMS/issues/441) |
| S19 Retention, export and deletion | Draft | — | — | — | — | — | [retention procedure](RETENTION_POLICY.md), [rights procedure](PARENT_DATA_RIGHTS_REQUESTS.md) |
| S20 Independent readiness review | Plan | — | — | — | — | — | [#173](https://github.com/Arete0920/Crown-CSMS/issues/173), [approval package](SOC2_APPROVAL_PACKAGE_20261008.md) |
| S21 SOC 2 Type I examination | Plan | — | — | — | — | — | [readiness plan](SOC2_READINESS_PLAN.md), [#173](https://github.com/Arete0920/Crown-CSMS/issues/173) |
| S22 SOC 2 Type II observation and report | Plan | — | — | — | — | — | [readiness plan](SOC2_READINESS_PLAN.md), [#173](https://github.com/Arete0920/Crown-CSMS/issues/173) |

### 8.2 Missing records, operating roles, decisions, and next feasible actions

Roles below are **proposed accountability**, not signed personnel appointments. Any action requiring owner, school, qualified counsel, vendor, or CPA approval stays pending until a dated record exists. Evidence is stored in restricted controlled custody; public GitHub may contain sanitized identifiers, hashes, UTC timestamps, findings and links only.

| ID / priority | Proposed operating role | Required missing record(s) | Approval needed | Next feasible action | Candidate ISO/IEC 27001:2022 reuse |
| --- | --- | --- | --- | --- | --- |
| S01 P1 | Founder/Product Owner | Signed accountability chart, control-owner/deputy appointments, oversight and acknowledgments | Executive approval; independent compensating review for solo-owner conflicts | Record primary/deputy assignments and first management review | Cl. 5.1, 5.3; A.5.2, A.5.3 |
| S02 P0 | Founder/Product Owner | Actual DEV/production boundary, Azure regions/services, data flows, customer commitments and communication population | Management scope/system-description signoff; CPA scope review later | Reconcile authenticated cloud inventory, shared modules and customer obligations | Cl. 4.1–4.4, 7.4; A.5.31 |
| S03 P0 | Founder/Product Owner | Current scored risk population, methodology, treatment owners/dates, residual-risk decisions | Management risk method, treatment and risk-acceptance signoff | Update scored risks for credential exposure, Azure PITR, tenant access, launch claims and single-operator dependency | Cl. 6.1.2–6.1.3, 8.2–8.3 |
| S04 P1 | Founder/Product Owner | Monthly reviewed exceptions population, dated minutes, action owners and retest approvals | Management review cadence and exception-closure authority | Review #104/#269/#427 and runtime-drift failures with evidence-linked CAPA decisions | Cl. 9.1, 9.3, 10.1–10.2; A.5.36 |
| S05 P0 | Founder/Product Owner | Effective approved versions, review schedule, communicated procedure set, documented exceptions | Dated management adoption and accountable control owner/deputy | Approve or revise policies, retention, incident targets and RTO/RPO in one recorded decision packet | Cl. 5.2–5.3, 7.5; A.5.1, A.5.37 |
| S06 P0 | Engineering/Operations | Complete reconciled Azure/CI/SaaS/devices/accounts/files/backup/vendor population, source-of-truth, regions and owners | Management scope confirmation and inventory owner | Authenticated read-only Azure DEV/production resource and provider inventory; classify absent/unverified assets | Cl. 4.3, 8.1; A.5.9, A.5.12, A.8.9 |
| S07 P0 | Engineering/Operations | Named actual account population, provider MFA proof, joiner/mover/leaver actions, quarterly and monthly access reviews | Access approvers, review scope/cadence and exception signoff | Export sanitized identity/account and MFA settings, review privileged grants and revoked identities | A.5.15–A.5.18, A.8.2, A.8.5 |
| S08 P0 | Engineering/Operations | Current deployed-SHA cross-tenant/role and denied-access population, support grant/expiry/revoke, break-glass records | School authorization, accountable support approvals and exception reviewer | Recheck newer family/role denials at exact accepted DEV SHA, then exercise grant/revocation without real-school exposure | A.5.15, A.5.18, A.8.3, A.8.29 |
| S09 P1 | Engineering/Operations | Actual provider physical-access assurance scope, managed-device population, disk encryption/patch/lock proofs | Provider assurance review; device baseline approval | Request provider assurance artifacts through restricted vendor channel and reconcile administrator devices | A.5.19, A.5.23, A.7.1–A.7.14, A.8.1 |
| S10 P0 | Engineering/Operations | TLS/encryption settings by live resource, key inventory/custody/rotation, residual consumer proof, DEV and historic Ed25519 closure | Key owners, exception/retirement and independent review of sensitive changes | Reuse #269 bounded DEV old/new credential test; resolve residual alternate consumers; #104 requires separate key/history disposition | A.5.17, A.5.33, A.8.24 |
| S11 P0 | Engineering/Operations | Approved severity SLAs, deployed scanner population, vulnerability inventory, response timestamps, retest/exceptions | Management SLA and residual-vulnerability approvals | Retain immutable CodeQL/dependency/gitleaks results for latest accepted head; reconcile findings to deployed assets | A.5.7, A.8.8, A.8.9 |
| S12 P0 | Engineering/Operations | Centralized actual event population, retention/immutability/access, test alert delivery, responder acknowledgment and coverage | Log retention, alert recipients and response roster | Inventory live logs without event payloads; test a harmless synthetic alert and record receipt/response | Cl. 9.1; A.8.15–A.8.17 |
| S13 P0 | Founder/Product Owner; Privacy/Legal reviewer | Adopted contacts, notification matrix, actual participants, timed tabletop, decision log and CAPA | Management severity/targets; qualified privacy/legal notification review | Schedule and document participant exercise for cross-tenant disclosure or leaked credential, with actual notification decision | A.5.24–A.5.28; A.6.8 |
| S14 P0 | Engineering/Operations | Live Azure restore target and backup/retention coverage, tested failure alerts, app/files/keys restore, timed RTO/RPO and rollback | Owner RTO/RPO and retention objectives, restore window and cleanup authority | Read-only target/activity-log/SKU diagnostic; choose approved available low-cost restore plan, isolate and time full Azure PITR without touching source | A.5.29–A.5.30, A.8.13–A.8.14 |
| S15 P0 | Engineering/Operations; Founder release decision | Current exact-head SHA parity, stale deploy queue disposition, approved rollback/migration and production authorization | Release owner decision, independent/compensating review; no bypass of protected checks | Confirm terminal stale queued run 40587751947, then governed current-main DEV parity and scoped rollback test | A.8.25, A.8.29, A.8.31–A.8.32 |
| S16 P1 | Founder/Product Owner; Privacy/Legal | Actual active vendor list/regions, assurance reports, signed contracts/DPAs, renewal and termination reviews | Vendor risk and contracting approver; processor activation separately prohibited | Reconcile GitHub/Azure and other actual subprocessors against contracts; keep CompuWerx planned, not activated | A.5.19–A.5.23, A.5.31 |
| S17 P1 | Founder/Product Owner | Workforce/contractor roster, signed NDA/acceptable-use records, training completion, role changes and independent deputy coverage | Management training baseline and responsibility allocations | Obtain restricted signed acknowledgments, dated training completions and compensating separation-of-duties review | Cl. 7.2–7.3; A.6.2–A.6.6 |
| S18 P0 before real schools | Privacy/Legal; School Success | Qualified applicability opinions, executed DPA/notices, school authorizations/consents, rights case population and real workflow tests | Legal/privacy approval, school authorization model and executed customer terms | Review age/customer/jurisdiction matrices; run synthetic school-controlled rights/consent negative workflow | A.5.31, A.5.34; A.8.3 |
| S19 P0 before real schools | Engineering/Operations; Privacy/Legal | Approved data-class schedules, request log and deletion/export results, holds, expiration, recovered-data replay test | Privacy/legal retention and hold signoff; school records authority | Approve schedule and rehearse a synthetic deletion plus backup-restore reapplication check | A.5.31, A.5.33, A.8.10 |
| S20 External | Founder sponsor; qualified independent reviewer | Reviewer engagement/independence, criterion-level findings, tested samples, remediation and closure | Reviewer selection and management disposition of all findings | Engage qualified independent reviewer after management owns scope/risk/evidence and obtain tracked findings | Cl. 9.2–9.3; A.5.35 (distinct ISO internal-audit requirements) |
| S21 External | Independent CPA; Founder management liaison | CPA engagement, scoped TSC criteria/system description, as-of date, management assertion, issued report | Management engagement/assertion; CPA independent report | Following readiness disposition, select CPA and agree on scope, date and readiness to test | No ISO substitute; Cl. 9.2–9.3 evidence may be reusable but not an ISO audit |
| S22 External | Independent CPA; named control owners | Approved observation period, recurring complete populations/samples, exceptions, CPA tests and issued report | Observation scope/period and actual independent CPA opinion | Start controlled recurring evidence retention only after procedures and owners are approved; engage CPA on period | No ISO substitute; Cl. 8–10 improvements can reuse evidence independently |

### 8.3 Bounded evidence disposition and October 29 / November 1 release impacts

1. **Release gate / source:** On inspected `c6caa580...`, check-runs were 35 success, 3 skipped and 1 DEV parity failure; [#504](https://github.com/Arete0920/Crown-CSMS/pull/504) later merged to `0093b07dd...` and must receive its **own** terminal required-check and source/deployed-identity decision. In contrast, an earlier [October 27 DEV hosted run 40593165189, attempt 2](https://github.com/Arete0920/Crown-CSMS/actions/runs/40593165189) passed 22 crawler, 13 buyer-flow and 15 synthetic two-tenant assertions (51 total) at **older deployed SHA** `63121646f6356eadea5e6f2f1bbe02081b2e1491`. It cannot certify current main or all role/family privacy cases.
2. **Recovery gate / specific coverage:** [October 27 isolated DEV-database recovery run 40584270959](https://github.com/Arete0920/Crown-CSMS/actions/runs/40584270959) has a recorded PASS for a real DEV database snapshot restored into **temporary PostgreSQL infrastructure**, with 467 tables and 245 migrations reconciled. In [#427 October 28 Azure managed-PITR reconciliation](https://github.com/Arete0920/Crown-CSMS/issues/427#issuecomment-6472158277), `Standard_B1ms` and `Standard_B2s` target restores both failed with `SkuNotAvailable`. No successful Azure managed-server PITR, full application/attachment/secret rollback, approved RTO/RPO measurement or backup retention operation is established. The policy's 8-hour RTO / 24-hour RPO / 30-day backup-retention figures remain **proposals**.
3. **Credential and history gate:** [#269](https://github.com/Arete0920/Crown-CSMS/issues/269) contains owner-provided restricted DEV rotation/wiring receipts and a limited live old-secret-rejected/new-secret-accepted reset-handler proof; remaining consumer/alternate-path disposition is OPEN. [#104](https://github.com/Arete0920/Crown-CSMS/issues/104) historical Ed25519 retirement/all-ref and distributable requirements are separately OPEN. [Merged #504](https://github.com/Arete0920/Crown-CSMS/pull/504) improves source-level observability credential redaction, not proof of deployed telemetry scrubbing or retired secret use.
4. **Release decision:** The October 29 technical-certification objective is **not yet accepted**; the strict deployed identity, managed PITR/rollback, required identity/tenant/owner/provisioning tests and security gates must be evaluated separately. The November 1 unrestricted production, real-school-data and payment activation decision remains **NO-GO** absent independent release authority. These are engineering/operator gates, **not** SOC 2 Type I/II assurance gates. Conversely, documenting SOC 2 work does not greenlight a deployment.
5. **Priority sequence / no duplicate work:** First reconcile stale queued DEV deployment run 40587751947, exact latest-head checks and safe runtime parity; in parallel gather read-only cloud/account/vendor inventory and owner management decisions. Then complete Azure-managed isolated PITR with measured recovery and alert validation, support/tenant revocation proof, and a participant tabletop. Existing successful CI snapshot exercises should be reused, **not rerun merely to increase test counts**. No source or issue checklist may be closed from this review alone.

### 8.4 ISO/IEC 27001 relationship (reuse, not equivalence)

The ISO references in section 8.2 are **candidate topic links**, not licensed criterion text, a complete Statement of Applicability (SoA), a determination of applicability, or independent ISO evidence. [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) as amended by [ISO/IEC 27001:2022/Amd 1:2024](https://www.iso.org/standard/88435.html) has separate management-system scope, leadership, risk, support, operations, internal-audit, management-review and improvement obligations (Clauses 4–10). Review relevant climate-change context/interested-party requirements under the amendment; do not presume applicability/outcome. [ISO issue #505](https://github.com/Arete0920/Crown-CSMS/issues/505) owns the complete 93-control Annex A SoA inventory, separate applicability justifications, impartial internal audit, management review, and accredited certification path. Each shared evidence item must be independently tested against the distinct objective and effective scope; a SOC 2 CPA report is not an ISO certificate, and the converse is also false.

**Disposition:** This is a source- and evidence-reference update for management decision preparation. It does not change the earlier October 23 reconciliation's original snapshot, approve any policy/operating control, or establish an independent report.

