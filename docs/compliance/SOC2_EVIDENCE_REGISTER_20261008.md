# CROWN SOC 2 Evidence Register

**Status:** SOURCE EVIDENCE RECONCILED / OPERATING EVIDENCE INCOMPLETE  
**Prepared:** 2026-10-08  
**Scope:** Current `main` source and repository-controlled documentation only  
**Boundary:** This register does not establish production operation, management approval, independent assurance, or a SOC 2 report.

## Evidence states

- **DESIGNED** — documented policy/procedure/control design exists.
- **IMPLEMENTED_SOURCE** — repository code/configuration implements the control objective.
- **VERIFIED_SOURCE** — executable repository evidence has previously demonstrated the control; current hosted-runner outage prevents fresh execution where noted.
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
| S15 change/release controls | PR discipline, release gates, repository policy; #158/#175/#176 security merges | IMPLEMENTED_SOURCE | Deployed identity evidence and fresh hosted-runner execution when service recovers |
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

## Current CI evidence limitation

On 2026-10-08, newly launched GitHub-hosted Actions jobs on both pull-request heads and `main` repeatedly failed before execution with `runner_id=0`, an empty runner name, and `steps=[]`. This is an infrastructure/admission condition, not executable test evidence. Prior executable workflow results remain valid historical evidence for the exact commits on which they ran, but no current-run success is claimed until hosted runners execute again.

## Readiness conclusion

CROWN has substantial documented control design and material repository-side security implementation. SOC 2 readiness is **not complete** until management approvals, actual production/environment evidence, recurring operating records, exercises, workforce/vendor records, independent readiness review, and the selected CPA engagement/report are completed.
