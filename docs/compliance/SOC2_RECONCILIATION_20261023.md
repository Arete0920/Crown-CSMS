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
