# CROWN SOC 2 Evidence Register

**Status:** SOURCE EVIDENCE RECONCILED / OPERATING EVIDENCE INCOMPLETE  
**Prepared:** 2026-10-08  
**Scope:** Source and repository-controlled documentation at `a091504ec4ce37c84037b51e15d9f909fcaf6f91`
**Reconciled:** 2026-10-08 after fresh exact-head Actions evidence  
**Boundary:** This register does not establish production operation, management approval, independent assurance, or a SOC 2 report.

## Evidence states

- **DESIGNED** — documented policy/procedure/control design exists.
- **IMPLEMENTED_SOURCE** — repository code/configuration implements the control objective.
- **VERIFIED_SOURCE** — executable repository evidence demonstrated the tested objective at an identified source SHA. The tested objective, run, job and result must be retained; this state does not prove runtime operation.
- **OPERATING_EVIDENCE_REQUIRED** — production/runtime/people/vendor evidence remains necessary.
- **EXTERNAL_REQUIRED** — independent or third-party evidence is required.

## Control evidence register

| Control | Current repository evidence | State | Remaining evidence |
| --- | --- | --- | --- |
| S01 governance/accountability | `SECURITY_OPERATING_POLICY.md`, `SOC2_READINESS_PLAN.md` | DESIGNED | Named people/deputies, approval record, recurring review evidence |
| S02 system description/communication | architecture and readiness documentation | DESIGNED | Approved system description, customer commitments, actual production boundary |
| S03 risk management | Security Operating Policy risk method; initial risk triage in readiness plan | DESIGNED | Approved scored assessment, treatments, residual-risk acceptance |
| S04 control monitoring | issue tracking, readiness matrix, corrective-action discipline | DESIGNED | Dated recurring management reviews and deficiency closures |
| S05 policy framework | Security Operating Policy plus dedicated incident/support/recovery policies | DESIGNED | Management approval/effective dates/acknowledgments |
| S06 asset/data/workforce inventory | repository architecture and data-domain documentation | DESIGNED | Actual deployed asset, SaaS, workforce, data-flow and ownership inventory |
| S07 access control | RBAC, tenant-scoped permission engine, role/permission seeding | IMPLEMENTED_SOURCE | Live named accounts, MFA evidence, joiner/mover/leaver records, access reviews |
| S08 tenant/support boundaries | tenant isolation controls; #158 explicit authority hardening; Support Access Policy | IMPLEMENTED_SOURCE | Deployed negative proof, support grants/revocations, break-glass exercise |
| S09 provider/device safeguards | policy requirements documented | DESIGNED | Provider assurance mapping and actual workforce-device evidence |
| S10 encryption/key management | production secrets architecture and policy requirements | DESIGNED | Deployed encryption-at-rest/TLS/key custody/rotation evidence; Ed25519 issue #104 must close separately |
| S11 vulnerability management | CodeQL, dependency audit, secret scan, license/dependency admission controls | IMPLEMENTED_SOURCE | Current production scan population, approved SLA operation, remediation history |
| S12 logging/monitoring | observability requirements and incident policy | DESIGNED | Central runtime log inventory, alert routing, retention, delivery test, responder coverage |
| S13 incident response | `INCIDENT_RESPONSE_POLICY.md` | DESIGNED | Approval, contacts, alert linkage, participant tabletop and corrective actions |
| S14 backup/recovery | `BACKUP_RESTORE_POLICY.md`, isolated PostgreSQL restore drill, recovery decision docs | DESIGNED | Current operational-backup identity, measured restore/RTO/RPO, approval |
| S15 change/release controls | PR discipline, release gates, repository policy; #158/#175/#176 security merges | IMPLEMENTED_SOURCE | Deployed identity, actual release authorization, rollback and recurring change-control evidence; fresh exact-head CI is now available for the reviewed SHA |
| S16 vendor/subprocessor management | `SUBPROCESSOR_REGISTER.md` and policy requirements | DESIGNED | Actual active-vendor reconciliation, contracts/DPAs, regions, annual review |
| S17 workforce security/training | policy and training requirements | DESIGNED | Actual confidentiality/acceptable-use acknowledgments and completed training |
| S18 privacy/terms/consent | privacy program, COPPA/FERPA/DPA documentation | DESIGNED | Qualified approval, executed terms/notices, actual consent/authorization evidence |
| S19 retention/deletion | retention policy and lifecycle requirements | DESIGNED | Approved schedule, request exercise, legal-hold and restored-data proof |
| S20 independent readiness review | requirement documented | EXTERNAL_REQUIRED | Independent readiness reviewer, findings, closure/disposition |
| S21 Type I report | requirement documented | EXTERNAL_REQUIRED | CPA scope/date/examination/report |
| S22 Type II report | requirement documented | EXTERNAL_REQUIRED | Observation period, recurring evidence, CPA examination/report |

## Recent security implementation evidence

- **#158** — explicit tenant and mutation authority plus tenant-persistence hardening.
- **#175** — finance authority, immutable financial facts, and fail-closed runtime administrator bootstrap.
- **#176** — explicit Spiritual Life mutation authority, negative view-only regressions, mutation-authority inventory, and repository verifier preventing new authentication-only mutation debt.
- **#167** — authentication throttle storage outages fail closed, including login and refresh-token paths.

These merges are source-control evidence. They do not substitute for runtime operating evidence.

## Reconciled exact-head CI evidence

The earlier 2026-10-08 runner-admission failures remain historical exceptions. They are no longer the latest evidence for the reviewed source head `a091504ec4ce37c84037b51e15d9f909fcaf6f91`.

All 11 workflows returned by the exact-head Actions query completed successfully: Release Authority Gates (37824630123), Repository Policy (37824630041), Repository Freshness (37824630130), Schema Governance (37824629972), Dependency Audit (37824630205), Release Verify (37824630148), CodeQL (37824630050), CI Tests and Checks (37824630085), Wizard E2E (37824630092), secret-scan (37824630178), and Tests (37824630118).

Tests job 113474162526 executed its test steps. Its log records **5,186 passed, 19 skipped, and 220 subtests passed**. A separate tenant-fixture step records 55 passed. Counts must not be added because suites may overlap. The Tests run completed at 2026-10-08T19:00:01Z. This is fresh source evidence, not assurance over deployment or every operational control. Workflow population is event/path dependent; 11 returned successes must not be described as every possible workflow executing.

The source implementation states for S07, S08, S11 and S15 may be supported by relevant passing checks at this SHA. Control-by-control assertions still require the actual test/output mapping. Operating evidence remains open. A subsequent documentation commit needs its own applicable checks.

## Reconciliation and approval package

See [SOC 2 approval package](SOC2_APPROVAL_PACKAGE_20261008.md) for proposed scope language, unassigned owner/deputy fields, eight risk-treatment records, hosting evidence requirements, operating acceptance criteria, and management decisions. Approval-ready means ready for management review; it does not mean approved or operationally ready.

## Readiness conclusion

CROWN has substantial documented control design and material repository-side security implementation. SOC 2 readiness is **not complete** until management approvals, actual production/environment evidence, recurring operating records, exercises, workforce/vendor records, independent readiness review, and the selected CPA engagement/report are completed.
