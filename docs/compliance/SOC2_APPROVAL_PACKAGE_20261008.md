# CROWN SOC 2 Scope and Evidence Package

Prepared October 8 2026 for management review and buyer diligence

DRAFT FOR APPROVAL   Management adoption and operational assurance remain open

CROWN has substantial documented security control design, merged security hardening, and fresh executable repository evidence. The October 8 reconciliation removes the stale claim that the current reviewed head lacks fresh CI. It does not establish an operating production environment, adopted policies, completed SOC 2 readiness, or an independent CPA report.

This package supplies proposed scope language, the 22-area evidence register, accountability fields, risk treatments, operating acceptance requirements, and specific decisions for management. January 1 2027 remains the commercial launch target; no assurance completion date is inferred from that target.

### Verified findings

| Evidence | Verified position |
| --- | --- |
| Repository baseline | a091504ec4ce37c84037b51e15d9f909fcaf6f91 |
| Exact-head CI | All 11 returned workflows succeeded. Tests run 37824630118 completed October 8 at 19:00:01 UTC. |
| Executed test log | 5,186 passed, 19 skipped, 220 subtests passed. Separate tenant-fixture step: 55 passed; populations may overlap. |
| Merged work | PRs 158, 167, 172, 174, 175 and 176 confirmed merged. |
| Hosting | Azure selected in repository planning. No current production inventory or runtime acceptance verified. |
| Open blockers | Issues 173 and 104 remain open. Named owners, approvals, actual operating evidence and independent assurance remain outstanding. |

### Statement suitable for investor materials

CROWN has a documented security and student-data privacy readiness program supported by merged repository security controls and fresh automated checks on an identified source baseline. SOC 2 preparation is in progress. Management approval, actual hosting and control operation, independent readiness review, and CPA examination remain separate requirements. No completed SOC 2 assurance or production certification is claimed.

## Proposed service scope

Proposed service organization: Arete Advisory Group LLC operating the CROWN Christian School Management Solution. Confirm the legal contracting entity against corporate records and the eventual CPA engagement before approval. The entity proposal is not an attestation of legal formation or executed customer terms.

Proposed initial product boundary: CROWN hosted school operations, enabled modules, portals, backend services, databases, file storage, background jobs, identity, network and secrets services, logging, monitoring, backup and recovery, administrative and support processes, source and change governance, and vendors that affect service security or customer data.

### Scope reconciliation

| Area | Disposition for approval |
| --- | --- |
| Hosting claim | The Azure first-release procedure explicitly says CROWN is undeployed. Current release authority asserts no successor production deployment or operational acceptance. Neither a template resource name nor CI is a live asset inventory. |
| Diadem | Proposed product exclusion pending documented infrastructure, contracts and data flows. Include shared infrastructure, customer data and security controls whenever they affect CROWN; a product label cannot remove these dependencies. |
| Payments | External processing remains disabled and unauthorized for activation. CROWN billing and financial records remain in the proposed data boundary. Metro is selected for planning only. |
| Existing services | GitHub is directly observed serving the repository and Actions. Inventory it as used for source/change governance; administration, contracts and assurance responsibilities still need review. |
| People and locations | Include actual administrators, support staff, contractors, workforce devices, work locations and restricted evidence storage. Planned staffing roles are not named appointments. |
| Trust Services | Security proposed initially. Evaluate Availability, Confidentiality, Processing Integrity and Privacy against customer commitments with the CPA. The 22 work areas are not 22 individual AICPA criteria. |

### System description and provider treatment

Approve a planning boundary now only if management wishes; finalize the deployed system description after the actual resource and data-flow inventory exists. Record customer commitments, enabled and disabled features, processing boundaries, locations, dependencies and changes. For each subservice organization, select and document the CPA-agreed carve-out or inclusive treatment and complementary controls. Identify school responsibilities for identity authorization, enrollment data, authorized support, notices and incident reporting without shifting CROWN obligations to schools.

The prior empty Render inventory is historical and limited to the inspected workspace. It was not repeated because the current connection has no selected workspace. It does not establish that every account or workspace is empty. No Azure connection or current resource export was available in this reconciliation.

## Hosting evidence required before operational approval

Priority is to identify the real environment before collecting screenshots or creating replacement infrastructure. Treat crown-rg, crown-api-prod, crown-api-dev and crownregistry as proposed identifiers until authenticated inventory verifies them. Do not approve production operation from a successful source test or collector exit code.

| Record | Minimum evidence and acceptance |
| --- | --- |
| H01 Authority | Authorized Azure tenant/subscription, organization relationship, region decisions, responsible human and deputy. Store full identifiers privately; publish sanitized references. |
| H02 Asset population | Timestamped export covering API, frontend, database, storage, registry, broker, worker, scheduler, identities, network, secrets store, logs and backups. Include stopped services and dependencies. Reconcile intended versus actual versus missing. |
| H03 Access | Complete privileged human/workload population, MFA or workload identity method, roles, least privilege, joiner/mover/leaver records, break-glass custody and denied-access tests. |
| H04 Data flows | Student, family, finance, health, pastoral and identity data; region, ingress/egress, vendors, exports, backup copies and deletion path. Identify disabled integrations separately. |
| H05 Configuration | TLS and storage/backup encryption, private connectivity, effective production settings, debug/bootstrap restrictions, key access and rotation evidence. Never collect secret values. |
| H06 Runtime identity | API and frontend full source SHA, immutable image digest, schema state, worker and scheduler identity, environment and release authorization. Confirm naturally scheduled task delivery, not only manual execution. |
| H07 Operating proof | Alert delivery with responder acknowledgement, denied tenant/role/support tests, backup failure alert, measured isolated restore of the selected environment and rollback evidence. |

### Existing read only collection route

The reviewed Azure Classroom Release Preflight workflow contains collector tests and a manual-only production inventory job. It uses existing Azure authentication, performs scoped metadata reads, and retains a seven-day artifact. No fresh manual inventory execution was verified here. The current callable connection did not provide workflow dispatch, and the workflow-run endpoint lookup was rejected; these access limits do not prove Azure is absent.

In an already authorized Azure CLI session, first identify the actual subscription. Then use the repository collector with that subscription, resource group and API app, and the selected verified SHA. Keep its JSON in restricted evidence storage. The collector excludes app settings and credentials; it is an initial inventory aid and does not cover all H01-H07 requirements or certify release acceptance.

Collection command: python scripts/ops/azure_classroom_preflight.py --subscription <confirmed-subscription> --resource-group <confirmed-resource-group> --api-app <confirmed-api-app> --expected-sha <verified-full-sha>

## Control accountability and adoption

Use the existing solo-maintainer model honestly. John C Megahan is a proposed accountable executive based on his stated owner role, not a recorded control appointment. No retrieved evidence establishes a named technical operator, deputy, privacy reviewer, independent readiness reviewer or CPA engagement. The September payment recap mentions a developer but does not establish current responsibility or appointment; no assignment is inferred.

| Role code | Proposed responsibility | Appointment field |
| --- | --- | --- |
| M | Management: scope, commitments, policies, risk decisions, resources and monthly readiness review. | Proposed John C Megahan; acceptance and effective date unrecorded. |
| O | Operations and engineering: inventories, access, runtime, releases, vulnerabilities, logs and recovery. | Named operator and deputy REQUIRED. |
| P | Privacy and contract review: applicability, terms, vendors, consent, retention and rights. | Named accountable reviewer and qualified adviser REQUIRED. |
| W | Workforce and school success: roster, training, acknowledgments and school communications. | Named person and deputy REQUIRED. |
| E | Evidence custodian: restricted repository, complete populations, retention, integrity and disclosure. | Named person and alternate REQUIRED. |
| I | Independent readiness reviewer and CPA: findings, engagement and examination. | Actual independent parties and engagement records REQUIRED. |

### Assignment record for every control

Record control ID, owner full name and role, deputy full name, appointment/acceptance date, effective date, capacity and access needs, reviewer, conflicts, cadence, escalation contact, restricted evidence location and review date. Every row in the register below uses a proposed role code, not an actual personnel assignment. Management remains accountable when duties are delegated.

### Independent review for a solo operator

The requester should not approve ordinary privileged access. If independent approval is unavailable, record the conflict, obtain the required school authorization and subsequent independent review under the support policy. Obtain qualified outside review of high-risk decisions and key-person continuity. Neither automation nor a second account establishes independent human oversight.

### Policy values requiring adoption

Existing proposals: daily backups; RPO no more than 24 hours; RTO within 8 hours; rolling backup retention 30 days; control evidence at least 12 months; ordinary support elevation at most 8 hours; emergency retrospective review within 1 business day. Review privileged access monthly and workforce access quarterly. Proposed vulnerability targets after triage: critical 48 hours, high 7 days, moderate 30 days, low 90 days. These are unapproved targets, not observed performance or customer promises. Stricter release gates remain controlling.

## Evidence register for governance and access

D = documented design verified present. S = source implementation identified by the register and merged work, with fresh CI at the reviewed SHA. X = external requirement. Every D or S control still requires management adoption and applicable operating evidence. Passing workflows do not prove every subcontrol. Role codes are unassigned proposals; mappings remain preliminary Common Criteria families in the readiness plan.

| ID and area | State | Role | Evidence required to close operating gap |
| --- | --- | --- | --- |
| S01<br>Governance | D | M | Named owner/deputy appointments, competence/ethics acknowledgments and dated oversight review. |
| S02<br>System description | D | M | Approved deployed boundary, commitments, communications, vendor treatment and school responsibilities. |
| S03<br>Risk assessment | D | M | Approved scores, treatment owners/dates, residual decisions and material-change review. |
| S04<br>Control monitoring | D | M | Dated monthly review, complete deficiency population, overdue escalation and verified closures. |
| S05<br>Policy framework | D | M | Approved versions, effective dates, schedule, exceptions and workforce acknowledgments. |
| S06<br>Asset data workforce | D | O | Actual H01-H04 populations, owners, software inventory and monthly reconciliation. |
| S07<br>Access controls | S | O | Live account/MFA population; grant/change/revoke samples; monthly privilege and quarterly access reviews. |
| S08<br>Tenant and support | S | O | Deployed cross-tenant/view-only denials; authorized support grant, expiry, session revocation, logs and break-glass exercise. |
| S09<br>Provider and devices | D | O | Provider report/responsibility review plus actual approved devices, encryption, lock and update evidence. |
| S10<br>Encryption and keys | D | O | Deployed TLS/encryption, human/workload permissions, rotation/revocation/recovery; separate issue 104 closure. |
| S11<br>Vulnerabilities | S | O | Deployed asset scan population, daily triage, approved SLA timestamps, remediation and rescans. |

S07 and S08 source support includes explicit tenant and mutation authority in PRs 158 and 176, finance/bootstrap work in 175, and fail-closed authentication-throttle handling in 167. S11 source support includes observed successful CodeQL, Dependency Audit and secret-scan workflows. Match individual test objectives to controls before assigning VERIFIED_SOURCE to an entire area.

## Evidence register for operations and assurance

| ID and area | State | Role | Evidence required to close operating gap |
| --- | --- | --- | --- |
| S12<br>Logs and monitoring | D | O | All log sources, integrity/access/retention, alert routing, delivery/acknowledgment test and response coverage. |
| S13<br>Incident response | D | O | Approved contacts, participant tabletop, timed notification decisions, corrective actions and retest. |
| S14<br>Backup and recovery | D | O | Operational backup identity and complete isolated restore; measured RTO/RPO, tenant/file/finance checks and deletion replay. |
| S15<br>Change and release | S | O | Actual release approvals, deployed SHA/digests, migration/rollback results and recurring change records. |
| S16<br>Vendors | D | P | Actual active vendor/data-flow inventory; signed terms/DPAs, regions, assurance review, notice and review dates. |
| S17<br>Workforce training | D | W | Actual roster, confidentiality/acceptable-use acknowledgments, training version/completion and access reconciliation. |
| S18<br>Privacy terms consent | D | P | Qualified applicability review, executed terms/notices, authorization/consent records and tested rights. |
| S19<br>Retention deletion | D | P | Approved schedules, export/delete/hold exercise, backup expiry and deletion replay before restored live use. |
| S20<br>Readiness review | X | I | Independent reviewer engagement, criterion-level assessment, findings and closure/disposition. |
| S21<br>Type I report | X | I | CPA-agreed scope/date and actual examination/report. No engagement or report verified. |
| S22<br>Type II report | X | I | CPA-agreed observation period, recurring population/evidence and actual examination/report. |

### Evidence record and acceptance rule

For each control retain: criterion mapping; approved procedure/version; owner and deputy; UTC capture time; environment; source SHA/digest where relevant; complete population or explained sample; restricted evidence reference and integrity hash; reviewer; result; exceptions; correction/retest; next due date; and closure approval. A self-authored assertion is not the required underlying record.

Retain customer personal information, credentials, device/account exports and sensitive contracts privately. Public repository records should contain sanitized references only. A 12-month evidence baseline remains proposed; confirm retention with contracts, holds and the auditor. Do not confuse evidence retention with the proposed 30-day customer backup window.

## Risk assessment and treatment decisions

Preserve the existing likelihood 1-5 times impact 1-5 method and planning scores. Bands: 1-4 Low, 5-9 Moderate, 10-16 High, 17-25 Critical. All eight risks remain OPEN and NOT APPROVED. Residual targets are goals, not measured or accepted residual risks. Fresh source CI removes one R08 evidence limitation; hosting, keys and operating proof still justify keeping the score provisional.

| Risk | Planning score | Role | Residual target |
| --- | --- | --- | --- |
| R01 Unauthorized customer access or mutation | 3 x 5 = 15 High | O | <=8 |
| R02 Data loss or recovery delay | 3 x 5 = 15 High | O | <=6 |
| R03 Containment or notification delay | 3 x 5 = 15 High | O | <=6 |
| R04 Uncontrolled vendor exposure | 3 x 4 = 12 High | P | <=6 |
| R05 Misleading readiness claims | 2 x 5 = 10 High | M | <=4 |
| R06 Key person dependence | 4 x 4 = 16 High | M | <=8 |
| R07 Retention consent or deletion mismatch | 3 x 4 = 12 High | P | <=6 |
| R08 Credential key or release compromise | 3 x 5 = 15 High | O | <=6 |

### Treatment closure evidence

R01  Confirm environment; run deployed tenant, view-only, restricted guardian and support expiry/revocation denials. Retain access population and reviewed exceptions.

R02  Inventory database/files/keys/dependencies; test backup failure alert; restore an identified operational backup in isolation and measure/reconcile full service.

R03  Approve contacts and coverage; inject an authorized alert; record acknowledgement/escalation; conduct participant tabletop and close findings.

R04  Reconcile actual vendors/regions/data flows and contract/assurance/customer obligations. Keep unapproved integrations disabled.

R05  Require scope/date/evidence labels and executive review of disclosures. Reserve report claims for an actual scoped CPA report.

R06  Appoint actual deputies, secure continuity access, rehearse handover and obtain independent review of material/conflicted decisions.

R07  Approve customer/feature/jurisdiction matrix and schedules; test rights, holds, backup expiry and deletion replay under qualified review.

R08  Keep issue 104 open until operational retirement/history/distributable proof exists; verify secret permissions/rotation and deployed identity; retain exact-head CI.

Every risk decision requires named owner/deputy, target date, interim controls, evidence reference, post-treatment likelihood and impact, management disposition, acceptance authority/expiry where relevant, and next review. All dates and signatures remain unrecorded. Hosting uncertainty is a prerequisite affecting R01-R04 and R08; assess it explicitly during final scoring. No acceptance may waive law, commitments, tenant isolation, release gates or independent assurance.

## Management decisions and operating sequence

| Decision | Required response |
| --- | --- |
| D01 Service organization | Confirm legal/contracting entity and approve the proposed CROWN planning boundary. Approver, date and effective date required. |
| D02 Actual hosting | Identify authorized Azure operator and tenant/subscription; approve regions and actual H01-H07 inventory. No inventory verified yet. |
| D03 Product and categories | Approve Diadem rationale and shared-dependency handling; confirm categories and customer commitments with CPA. |
| D04 Accountability | Name M/O/P/W/E owners, deputies and independent reviewer. Record acceptance, coverage and conflicts. |
| D05 Policy and risk | Approve policy versions, targets, schedules, risk scores/treatments/dates and residual authority. No risk acceptance recorded. |
| D06 Evidence and vendors | Choose restricted evidence location/custodian and retention; approve actual vendor/contracts/notice records. |
| D07 Independent assurance | Select readiness reviewer and CPA, review type/scope/date or period and engagement budget. No report deadline promised. |

### Recommended sequence

First confirm D01-D04 and collect the actual environment inventory using existing authorized read access. This permits management to finalize the system description, access population, data flows and vendor treatment. In parallel, the named custodian can retain the current source evidence and management can adopt reviewed policy and risk values.

Next verify the selected environment, identities, encryption, keys, deployed revision and monitoring. Run alert delivery and support/revocation tests, then a participant incident tabletop and a measured isolated full restore. Record failures and retest; do not use fabricated timestamps or synthetic backup inputs as operational results.

Complete workforce and executed contract/privacy records, conduct dated recurring reviews, and obtain the independent readiness assessment. Resolve or properly disposition findings and agree the CPA examination. Type I evaluates the specified date; Type II requires operating-effectiveness evidence over the agreed period. The CPA determines the actual engagement requirements.

### Approval record

Management decision status: NOT RECORDED. Approver name and role: ____________________. Scope/version approved or revised: ____________________. Approval and effective dates: ____________________. Named assignments and treatment dates attached: ____________________. Next review date: ____________________.

Signing a planning scope does not certify production operation, close issue 173, clear issue 104, activate payments, or issue SOC 2 assurance. Record those separate outcomes only against their acceptance evidence.

## Evidence references and reconciliation record

Assessment basis: exact source a091504ec4ce37c84037b51e15d9f909fcaf6f91. Findings are bounded to the retrieved repository, current workflow records, the October 7 readiness PDF and the September 30 payment meeting recap. No live Azure resource export, signed agreement, management approval, workforce training record, completed operating exercise or CPA report was verified in these records. Search non-results are access limitations, not proof that a record does not exist.

E01  Scope decision

https://github.com/Arete0920/Crown-CSMS/blob/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/compliance/SOC2_SCOPE_DECISION_20261008.md

E02  Risk assessment

https://github.com/Arete0920/Crown-CSMS/blob/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/compliance/SOC2_RISK_ASSESSMENT_20261008.md

E03  Evidence register

https://github.com/Arete0920/Crown-CSMS/blob/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/compliance/SOC2_EVIDENCE_REGISTER_20261008.md

E04  Release authority

https://github.com/Arete0920/Crown-CSMS/blob/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/CURRENT_RELEASE_STATUS.md

E05  Azure first hosted release

https://github.com/Arete0920/Crown-CSMS/blob/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/operations/AZURE_CLASSROOM_FIRST_RELEASE.md

E06  Policies and execution register

https://github.com/Arete0920/Crown-CSMS/tree/a091504ec4ce37c84037b51e15d9f909fcaf6f91/docs/compliance

E07  Fresh Tests run and executed job

https://github.com/Arete0920/Crown-CSMS/actions/runs/37824630118/job/113474162526

E08  Operating readiness issue

https://github.com/Arete0920/Crown-CSMS/issues/173

E09  Key retirement and history blocker

https://github.com/Arete0920/Crown-CSMS/issues/104

E10  Merged security and compliance work

PRs 158, 167, 172, 174, 175, 176; merge metadata retrieved October 8.

E11  Payment planning record

September 30 Fathom recap of Metro Payment Technologies meeting. Read-only review supports planning; gateway/compliance follow-up remained open.

E12  Prior investor readiness summary

CROWN_Investor_Security_Privacy_Compliance_Readiness_2026-10-07.pdf; all four pages reviewed.

E13  AICPA system and report description

https://www.aicpa-cima.com/resources/download/illustrative-soc-2-r-report-with-description-and-assertion

### Discrepancies resolved in this package

The earlier current-CI outage statement is superseded for the reviewed SHA; all 11 returned workflows succeeded and Tests actually executed. R08 retains unresolved production-key/history/deployment requirements. The scope identifies the source of the undeployed statement and limits Render claims to a historical inspected workspace. Actual GitHub use is separated from unverified candidate hosting and integration vendors. Diadem exclusion does not remove shared dependencies; disabled processing does not exclude CROWN financial data. Every appointment, target, risk score and approval retains its correct proposed or unapproved status.

Repository revisions accompanying this package are documentation proposals until merged. Their own applicable checks must be reviewed separately. This package adds no production authorization, management signature, risk acceptance or assurance report.
