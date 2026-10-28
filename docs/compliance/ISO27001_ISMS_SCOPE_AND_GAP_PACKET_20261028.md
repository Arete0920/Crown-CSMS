# CROWN ISO/IEC 27001:2022 ISMS — scope, gap and evidence packet

**Status:** WORKING PROPOSAL / NOT MANAGEMENT APPROVED / NOT CERTIFIED  
**Prepared:** 2026-10-28  
**Controlling issue:** [#505](https://github.com/Arete0920/Crown-CSMS/issues/505)  
**Related SOC 2 program:** [#173](https://github.com/Arete0920/Crown-CSMS/issues/173)  
**Repository inspection baseline:** `main` at `0093b07dd37cd494d46b83fc83cb563217dda936` (not a claim about later revisions)  
**Related, separate evidence work:** [draft PR #507](https://github.com/Arete0920/Crown-CSMS/pull/507) — proposed S01–S22 evidence maturity and ISO reuse candidates; not assumed merged or accepted.

## 1. Authority, purpose and truth boundary

This packet starts ISO-specific *management-system* assessment; it does not confer control acceptance, an approved Statement of Applicability (SoA), an audit opinion, or ISO certification. Existing SOC 2 evidence may be referenced once from controlled custody, but an AICPA observation cannot automatically satisfy an ISO requirement or a control-effectiveness test.

Applicable publication references:
- [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) — requirements and Annex A reference controls.
- [ISO/IEC 27001:2022/Amd 1:2024](https://www.iso.org/standard/88435.html) — climate-action changes to management-system context and interested-party consideration.
- [ISO/IEC 27002:2022](https://www.iso.org/standard/75652.html) — supporting implementation guidance.
- The full authorized normative requirements and control descriptions have **not** been verified as available to this review. A qualified reviewer with lawful access must verify the final control mapping, text version, and clause-level test requirements before approval. No proprietary control descriptions are reproduced here.

The companion [93-row SoA register](ISO27001_ANNEX_A_SOA_REGISTER_20261028.csv) contains only Annex A identifiers and working assessment fields. All applicability values are `UNASSESSED`. The 93 entries are *inventory coverage*, not 93 applicable controls, 93 implemented controls, a score, or evidence of suitability.

## 2. Proposed ISMS boundary — decision requested

**Proposed legal organization:** Arete Advisory Group LLC. Confirm legal entity, customer contracting obligations, jurisdiction, and management approver from authoritative records before adoption.

**Proposed service:** Design, development, provision, administration, support, change governance and security operations for CROWN Christian School Management Solution and its enabled school-management workflows. The proposed boundary follows information and control dependencies rather than only application names or customer-visible features.

| Boundary dimension | Working proposal | Verification / approval gate |
| --- | --- | --- |
| Product and data | Include CROWN school/tenant administration; parent, student, teacher and administrator flows; education, family, personnel, health/counseling/pastoral, financial aid, billing, survey, analytics and document data where actually processed | Reconcile actual enabled modules, customer contracts, legal bases and data flows against [regulated-data inventory](REGULATED_DATA_INVENTORY.md); do not equate source surfaces with production use |
| Technology and environments | Include relevant application/frontend, Django/API, workers/brokers, databases, files, logging, deployment and backup components, encryption/key custody, GitHub/source and CI/CD, security monitoring, endpoints and identity tools | Authenticated inventory of *actual* DEV and any production infrastructure, accounts, regions, owners, network/deployment paths and immutable deployed identities; do not extrapolate DEV to production |
| People, premises and processes | Include actual founder/operator, staff, contractors, support, privileged administration, remote-work devices/locations, joiner-mover-leaver, incident and continuity duties, management review and restricted-evidence custody | Workforce/device/location roster, access rights, deputy/segregation review, competent reviewers, actual agreements/acknowledgments and role appointments |
| Vendors and shared controls | Include actual infrastructure, identity, repository, telemetry and service providers and applicable subservice/shared-responsibility controls | Reconcile active vs planned vendors, data regions, contracts/DPAs, independent reports, controls, owner and customer dependencies in [subprocessor register](SUBPROCESSOR_REGISTER.md) |
| Diadem | Propose **standalone Diadem service outside initial CROWN product certification boundary**, subject to documented separate hosting, processing and contracts; **shared CROWN controls/data are not excluded** | Management approval after dependency/data-flow analysis; if Diadem uses in-scope systems or shares controls, retain those dependencies and reconsider the product boundary |
| Jireh and other CROWN modules | Include CROWN-hosted financial-aid functions and any actual shared Jireh identities, data, infrastructure and control dependencies; a separate standalone service has **no automatic exclusion** | Confirm implementation/hosting and school-data flows before final disposition; apply the same dependency analysis to Kairos, Scribe, Solomon and other modules |
| CompuWerx/payment processing | Intended payment partner only. Source/vendor records describe payments as **disabled, fail closed and not approved for live activation**; payment enablement/change governance and existing billing data remain relevant | Provider/merchant/processor legal roles, signed terms, PCI responsibility, actual data flows and activation decision required before any in-scope live gateway claim |
| Microsoft 365 and future integrations | Planned or enabled integration dependencies only to the extent established by actual configurations and data flows | Confirm active identity/tenant/permission populations, vendor agreements, regional location and customer approvals; future plans alone are not operational services |
| Information and evidence locations | Include restricted operational evidence holdings and workforce access paths in the final ISMS boundary, but publish only nonsensitive index metadata here | Management-approved restricted repository, custodian, role-based access, retention, integrity, disclosure, incident and backup controls |

**Proposed boundary statement (NOT APPROVED):** "The Arete Advisory Group LLC information security management system governing the design, development, hosted provision, administration, support, and protection of the CROWN Christian School Management Solution, its in-scope processing and enabling workforce, technology, facilities, service providers, and shared security processes, as identified in the approved system and asset inventories."

This is intentionally **conditional**: final organizational boundaries, physical locations, legal entities, enabled services, shared dependencies, interfaces and justified exclusions cannot be approved from source documentation alone. The current [SOC 2 scope draft](SOC2_SCOPE_DECISION_20261008.md) is a starting reference, **not** approval of this ISO scope. Historical Azure DEV observations are recorded in [release status](../CURRENT_RELEASE_STATUS.md) and [#273](https://github.com/Arete0920/Crown-CSMS/issues/273); current authenticated control-plane and full production-boundary acceptance are not established.

## 3. Clause 4–10 management-system gap map

This is a summary of known record-level gaps, **not** a completed licensed-clause audit. `D` = document found or planned; `A` = approved; `S` = source tested; `R` = selected deployed runtime verified; `O` = recurring operating verified; `E` = independently assessed. A dash means **not evidenced in this inspection**, not demonstrably absent or failed. The entry in the first column describes clause groups, not an authoritative reproduction of normative criteria.

| Clause / topic | Inspected basis | ISO-specific open gate | Highest supportable state for this clause packet |
| --- | --- | --- | --- |
| 4 — Context and ISMS scope | SOC 2 draft scope; regulated-data and vendor inventories | Actual parties, needs, boundaries, interfaces and dependencies; record the Amendment 1 climate-change relevance decision and interested-party requirements with rationale; management-approved scope | D only |
| 5 — Leadership and information-security governance | [security operating policy](SECURITY_OPERATING_POLICY.md) is a draft | Signed management policy/commitment, objectives, responsibilities, authority, resources, actual accountable leader and deputies | D only |
| 6 — Risk and objectives | [historical R01–R08 risk draft](SOC2_RISK_ASSESSMENT_20261008.md), proposed 1–5 method | Adopt methodology, criteria and thresholds; perform current scope-based risk assessments; record selected treatments, residual dispositions and measurable objectives; approve SoA | D only |
| 7 — Support and documented information | Policy and process drafts | Competence/awareness/communications; training and confidentiality receipts; controlled document approval, access, changes, retention and evidence integrity | D only |
| 8 — Operation | Technical repository protections and dated, bounded source/recovery observations | Operate approved risk assessment/treatment plans; verify selected-environment assets, access, monitoring, vendors, recovery and records at actual cadence | D; some separate bounded S records exist, not clause completion |
| 9 — Monitoring, internal audit and management review | GitHub check records and SOC 2 readiness tracking | Approved measurement plan/results; qualified **impartial ISO internal audit** with findings; dated management review inputs, decisions and follow-up | D; A/O/E not verified |
| 10 — Nonconformity, corrective action and improvement | Issues and engineering defect-remediation workflow | Formally record ISO nonconformities, root cause, responsible owner, due dates, verified corrective effectiveness, and improvement decisions | D; recurring ISO effectiveness not verified |

**Amendment 1 decision record (OPEN):** Identify climate-related factors, whether climate change is relevant to the intended ISMS outcome, whether interested parties have climate-related requirements, supporting assessment and approval. **No relevance or non-relevance outcome is presumed.**

## 4. Reuse inventory — existing record, not automatic ISO evidence

The evidence inventory below links existing *source records*, not customer records or private operational exports. `D` means the cited documentation was inspected; `S historical` describes a dated bounded source exercise noted in the record, not a control-level finding or a new independent verification. `A/R/O/E` require separate review of actual approvals and test populations. Do not copy these into 93 SoA rows until a licensed-control-specific mapping is justified.

| Reference | Source record and inspected meaning | Supported classification | Gap / custody |
| --- | --- | --- | --- |
| I-01 | [SOC 2 scope proposal](SOC2_SCOPE_DECISION_20261008.md) — legal/product/hosting boundary draft | D; not adopted | Actual entity, regions, shared products and ISMS approval |
| I-02 | [Security Operating Policy](SECURITY_OPERATING_POLICY.md) — risk, access, vendor, response and change procedure drafts | D; adoption open | Approved version, workforce acknowledgments and actual operation |
| I-03 | [SOC 2 risk assessment](SOC2_RISK_ASSESSMENT_20261008.md) — R01–R08 with draft likelihood/impact/treatments | D; scores unapproved | Reassess under approved ISO method and scope; accept treatments/residual risks |
| I-04 | [Regulated Data Inventory](REGULATED_DATA_INVENTORY.md) — repository-bounded data subjects and processing surfaces | D; source paths referenced | Authenticated storage, recipients, regions, retention and deployed flow evidence |
| I-05 | [Subprocessor Register](SUBPROCESSOR_REGISTER.md) — candidate and intended vendors with activation caveats | D; active roster unverified | Executed agreements, actual providers, regional location, assurance and rights |
| I-06 | [SOC 2 reconciliation](SOC2_RECONCILIATION_20261023.md) and [historical evidence register](SOC2_EVIDENCE_REGISTER_20261008.md) | D; historical S evidence described | Source versions/timestamps/test objectives and actual runtime/operating samples |
| I-07 | [Release status](../CURRENT_RELEASE_STATUS.md), [#273](https://github.com/Arete0920/Crown-CSMS/issues/273) and [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) — historic DEV testing, live drift/recovery blockers | D; prior bounded hosted S/R observations are environment/SHA-specific | No current complete Azure control-plane proof or production/certification inference |
| I-08 | [Isolated PostgreSQL restore run](https://github.com/Arete0920/Crown-CSMS/actions/runs/39165456638) as documented in [#173](https://github.com/Arete0920/Crown-CSMS/issues/173) | Dated generated-fixture source exercise reported | NOT an operational backup, measured service RTO/RPO, or Azure PITR proof |
| I-09 | [SOC 2 compliance matrix](COMPLIANCE_MATRIX.md), [privacy/legal matrix](PRIVACY_LEGAL_RECONCILIATION_MATRIX.md) | D; source and obligation inventory | Customer-specific legal applicability and approved contractual evidence |
| I-10 | [Draft PR #507](https://github.com/Arete0920/Crown-CSMS/pull/507) — candidate shared S01–S22 evidence-maturity/crosswalk update | DRAFT proposal at preparation | Reuse only after normal PR acceptance; never interpret S01–S22 as Annex A or AICPA criterion equivalents |
| I-11 | [Incident Policy](INCIDENT_RESPONSE_POLICY.md), [Support Access Policy](SUPPORT_ACCESS_POLICY.md), [Backup/Restore Policy](BACKUP_RESTORE_POLICY.md) | D; procedures located | Approved roles, current operational populations, exercises, actual successful recovery |

**Public evidence custody rules:** Only non-sensitive path references, redacted IDs, evidence digests, control results and dates belong in this repository. Retain actual workforce names/rights, private contracts, student/family records, credentials, key material, Azure topology and sensitive findings in approved access-controlled storage. Each operating item needs a collector, approver/reviewer, UTC timestamp, relevant scope/population, immutable integrity receipt, retention and lawful disclosure rule. No restricted evidence repository or custodian is approved by this packet.

## 5. Risk inventory and SoA construction rules

The eight current risks `R01`–`R08` are **draft planning scenarios**, not signed ISO risk assessments or accepted residual scores. Their themes are: unauthorized cross-tenant access (R01); unrecovered data/service (R02); delayed incident action (R03); vendor exposure (R04); unsupported assurance claims (R05); key-person dependence (R06); privacy lifecycle mismatch (R07); and credential/key/release compromise (R08). See [draft risk assessment](SOC2_RISK_ASSESSMENT_20261008.md).

For each Annex A entry in the [SoA CSV](ISO27001_ANNEX_A_SOA_REGISTER_20261028.csv):
1. Verify identifier and associated detailed requirement against lawfully accessed, version-controlled ISO/IEC 27001:2022 Annex A and applicable 27002 guidance. Document licensed-source reviewer/version; do not paste protected text into public Git.
2. Evaluate actual applicability against the **approved** organizational/technology/people/physical boundary, interested parties, law/customer terms, identified risks and treatments; justify both inclusion and exclusion individually, without defaulting to applicable or excluding for a favorable score.
3. Link an approved risk identifier and treatment decision, **real appointed owner/deputy**, testing frequency and procedures. Map SOC 2 S01–S22 only as independently substantiated evidence candidates.
4. Record separately **design documented, management approved, implemented/source tested, selected-runtime verified, recurring operation, independent assessment**. Record scope, objective, timestamps, population, failed cases, reviewer and restricted evidence pointer; absence of evidence must not be treated as implementation failure.
5. Review all 93 entries, decisions and any additional organization-specific risk treatments/control requirements. Obtain management approval of the final SoA and reassess after material change.

**CROWN-specific treatment candidates, outside any claim of Annex A equivalence:** deployed cross-school and co-guardian denial checks (R01); school-authorized support grant/expiry and emergency access (R01/R06); deletion and backup-restoration propagation for school/family records (R02/R07); disabled-to-enabled payment change authorization (R04/R08); and revocation/clean distributable verification for the historical trust-key matter [#104](https://github.com/Arete0920/Crown-CSMS/issues/104) (R08). These are *proposed local tests*, not accepted ISO control statements. Resolve [#269](https://github.com/Arete0920/Crown-CSMS/issues/269) and related access/credential evidence separately.

## 6. Decision and execution register

| Gate | Required decision / evidence | Proposed accountable role (NOT appointment) | Current disposition |
| --- | --- | --- | --- |
| M01 | Approve legal entity, organizational context, interested parties and exact ISMS boundary; resolve Jireh/Diadem/shared-system treatment | Founder / ISMS management | OPEN; proposal only |
| M02 | Confirm authoritative licensed ISO criteria and mapping/reviewer; assess Amendment 1 climate context and interested parties | ISMS management + qualified ISO reviewer | OPEN |
| M03 | Adopt security policy, measurable objectives, risk methodology, acceptance thresholds and change/reassessment cadence | Executive management / risk owner | OPEN |
| M04 | Appoint named ISMS leader, control owners/deputies, assessor/evidence custodian and conflict-of-interest safeguards | Executive management | OPEN |
| M05 | Approve actual asset/workforce/physical/cloud/system/vendor and information-flow inventories including customer contracts | Engineering/Operations + Privacy/Legal | OPEN |
| M06 | Approve risks/treatments, any non-Annex controls and all 93 individual SoA applicability decisions | Risk owners + management; qualified reviewer | OPEN |
| M07 | Designate restricted evidence system and approve retention/access/integrity; collect identity/access/MFA/changes/logging/responder/recovery samples | Evidence custodian + Operations | OPEN |
| M08 | Conduct impartial internal audit, document nonconformities and corrective effectiveness | Competent independent internal-audit function | NOT VERIFIED |
| M09 | Complete dated management review with follow-up | Executive management | NOT VERIFIED |
| M10 | Select appropriately accredited certification body; complete Stage 1 and Stage 2, resolve findings and retain scope-bearing certificate | Executive management + independent body | NOT VERIFIED — NOT CERTIFIED |

**Execution order without duplicate work:** (a) finalize this draft decision packet and validate the 93-row inventory; (b) obtain management boundary and normative-access decisions; (c) coordinate approved risk/SoA mapping and evidence reuse with #173 and PR #507; (d) collect non-cloud governance/people/vendor proofs where permitted; (e) obtain authenticated Azure/identity/recovery evidence when the separately governed cloud work resumes; (f) conduct actual internal audit and management review; (g) seek accredited certification assessment only when ready. Deprioritizing Azure investigation cannot count as passing its corresponding control gates.

## 7. Verification and claim restrictions

- This draft includes **37 A.5, 8 A.6, 14 A.7 and 34 A.8 identifiers = 93 distinct entries**, all initially `UNASSESSED`.
- No management signatures, current operating controls, independent ISO internal audit, management review, or certification were created or observed by this documentation task.
- Closing documentation or merging a source-only PR advances planning records, **not** operational control effectiveness or certification. Issue #505 remains open.
- External ISO certification, if ultimately earned, applies only to the certificate's exact organizational/service scope and validity period. It cannot substitute for school/tenant privacy-law determinations, PCI obligations, SOC 2 examination or production release authorization.
