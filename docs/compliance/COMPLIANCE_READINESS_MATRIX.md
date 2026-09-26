# CROWN Compliance Readiness Matrix

**Status:** Compliance-readiness working record  
**Owner:** CROWN Engineering / Product Owner  
**Purpose:** Map current technical and organizational controls to the principal security and student-privacy obligations relevant to CROWN.

## Important boundary

This document is a readiness and evidence map. It is not a legal opinion, regulator approval, FERPA certification, COPPA certification, HIPAA certification, PCI certification, or SOC 2 report.

## Frameworks and obligations in scope

### SOC 2
CROWN will prepare against the AICPA Trust Services Criteria, beginning with the Security category and evaluating Availability, Confidentiality, Processing Integrity, and Privacy for inclusion based on customer commitments and system scope.

### FERPA-aligned school-vendor controls
Where FERPA applies to a customer or covered records, CROWN's school-service model must support the school-official / outsourced-service conditions, including school control over education-record use and maintenance, purpose limitation, and restrictions on redisclosure.

### COPPA
Where CROWN collects personal information online from children under 13, collection must be limited to the educational purpose authorized by the school or otherwise supported by valid parental consent. School authorization cannot be used to justify unrelated commercial use.

### PPRA
Where a customer is subject to PPRA, CROWN must support school policies and parental rights relating to protected surveys, access, notice, and privacy safeguards.

### State student-privacy laws
A state-by-state contract and control overlay is required before national rollout. CROWN should maintain a contract matrix covering data ownership, advertising restrictions, sale/profiling restrictions, deletion, breach notice, subcontractors, parental rights, and security commitments.

### PCI DSS
CROWN should minimize PCI scope by using a qualified payment processor and avoiding storage or direct handling of sensitive payment-card authentication data. The final PCI obligation depends on the selected payment architecture and processor contract.

### HIPAA edge cases
HIPAA is generally not the governing privacy rule for elementary/secondary student health records that are FERPA education records, but HIPAA can apply in some private-school or health-provider configurations. CROWN should classify the customer and data relationship before enabling health integrations that could create HIPAA obligations.

## Control matrix

| Domain | Current Crown foundation | Required evidence / gap | Priority |
|---|---|---|---|
| Governance | Change management, exact-head release controls, engineering accountability | Formal security/compliance charter, assigned control owners, annual review cadence | P0 |
| Risk management | Security gates, dependency scans, CodeQL | Documented annual and change-triggered risk assessment; risk register; treatment decisions | P0 |
| Asset inventory | Architecture map and repository inventory | Production asset inventory including cloud services, databases, endpoints, SaaS, secrets, and owners | P0 |
| Data inventory | Student/family/staff domains documented | Data-flow map, data classification, field-level regulated-data inventory, source/use/destination/retention | P0 |
| Access control | Authentication, RBAC, tenant isolation | Joiner/mover/leaver process, privileged-access review, MFA evidence, periodic access recertification | P0 |
| Tenant isolation | Canonical tenant boundary, tests and CI gate | Production evidence, negative-test suite, cross-tenant incident playbook | P0 |
| Change management | PR and exact-head controls | Required reviewers/approvers matrix, emergency-change path, release evidence retention | P1 |
| Secure development | Test gates, dependency and static analysis | Secure coding standard, threat modeling for material changes, vulnerability SLAs | P1 |
| Vulnerability management | CodeQL, dependency audit, secret scan | Scan cadence, severity SLA, exception process, remediation evidence | P0 |
| Logging/audit | Audit architecture and structured logging | Central log inventory, retention, immutable/security-event coverage, alert ownership | P0 |
| Incident response | Operational/recovery documents | Formal incident-response plan, privacy/breach decision tree, tabletop evidence, notification matrix | P0 |
| Business continuity | Rollback/restore mechanics | Current backup schedule, restore tests, RTO/RPO targets, disaster-recovery exercise evidence | P0 |
| Vendor management | External integrations identified | Subprocessor inventory, security review, DPAs, data locations, breach terms, annual reassessment | P0 |
| Privacy notices | Existing claim boundaries | Customer DPA, privacy notice, student/parent notice support, subprocessor disclosure | P0 |
| Purpose limitation | Domain-specific application design | Contractual and technical restrictions against advertising/sale/unrelated commercial use | P0 |
| Data minimization | Some feature-level control | Collection justification by field/domain; optional-field review; telemetry minimization | P1 |
| Retention/deletion | Retention task exists | Approved retention schedule; customer deletion workflow; backups/deletion handling; evidence logs | P0 |
| Parent/student rights | Portals exist | Access/correction/export/deletion request procedures with school-controlled workflow | P0 |
| COPPA consent | School-controlled product model | Verified school authorization workflow; direct-parent consent workflow for non-school-authorized collection | P0 |
| FERPA vendor terms | Tenant/data controls exist | FERPA-aligned DPA language: direct control, legitimate educational purpose, redisclosure restrictions, return/deletion | P0 |
| PPRA | Survey/content features may exist | Protected-survey classification, parental inspection/notice/opt-out support where applicable | P1 |
| Health data | Nurse/health module boundaries | FERPA/HIPAA applicability decision tree, restricted roles, minimum necessary access, integration review | P0 |
| Payment security | Payment processing disabled | Processor architecture, PCI responsibility matrix, tokenization/hosted payment evidence | P0 before activation |
| Encryption | HTTPS/DB SSL configuration present | Encryption-at-rest evidence, key-management inventory, rotation/access evidence | P0 |
| Availability | Health/release checks exist | SLOs, uptime monitoring, alert escalation, incident/postmortem process | P1 |
| Confidentiality | RBAC/tenant controls | Confidentiality classification and handling requirements across exports, support, backups | P1 |
| Processing integrity | Tests and finance verification | Critical workflow reconciliation, idempotency controls, data-integrity exception monitoring | P1 |
| Training | Not yet evidenced | Annual security/privacy training and role-specific training evidence | P0 |
| Policy management | Multiple engineering policies | Formal policy set with version, owner, approval date, review date, acknowledgment evidence | P0 |

## Immediate evidence package

Before engaging a SOC 2 auditor, assemble:

1. system description and architecture/data-flow diagrams;
2. control inventory mapped to Trust Services Criteria;
3. risk assessment and risk register;
4. asset, software, vendor, and subprocessor inventories;
5. access-control and privileged-access evidence;
6. SDLC/change-management evidence;
7. vulnerability and patch-management evidence;
8. logging/monitoring and incident-response evidence;
9. backup/restore and continuity evidence;
10. privacy/data-retention/deletion evidence;
11. employee security/privacy training evidence;
12. customer DPA/privacy notice/subprocessor terms;
13. FERPA/COPPA/PPRA operational procedures;
14. production environment evidence tied to exact source identity.

## Readiness disposition

CROWN has strong technical foundations for a compliance program, but formal SOC 2 and student-privacy readiness depends on operational evidence, contracts, policies, production configuration, and repeated control performance over time.
