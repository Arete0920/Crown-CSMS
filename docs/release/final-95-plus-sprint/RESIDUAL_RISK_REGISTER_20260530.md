# CROWN Final 95+ Residual Risk Register - 2026-05-30

Status: ACTIVE FINAL-SPRINT RISK REGISTER
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This register captures residual production-readiness concerns that are not yet explicit enough in the final sprint control stack. A risk listed here is not automatically a defect, but it must be classified, accepted, mitigated, or closed with evidence before unrestricted production release.

## Decision rule

No residual risk can be silently ignored. Each row must become one of:

- PASS with evidence,
- NOT APPLICABLE with rationale,
- ACCEPTED RISK with owner and reason,
- NOT DONE and blocking.

## Residual risks requiring explicit closure

| ID | Risk area | Why it matters | Current status | Required closure artifact |
|---|---|---|---|---|
| RR-01 | Performance and load capacity | A production school system must handle concurrent parent, student, staff, dashboard, import, and billing traffic without degraded core workflows | NOT DONE | `FINAL_PERFORMANCE_LOAD_PACKET.md` |
| RR-02 | Observability and incident operations | Production support requires health, logs, metrics, trace/correlation IDs, alerts, escalation, and runbook clarity | PARTIAL / NOT VERIFIED | `FINAL_OBSERVABILITY_INCIDENT_PACKET.md` |
| RR-03 | Dependency, license, and SBOM hygiene | Marketplace readiness requires dependency risk visibility, license review, and vulnerable package remediation | NOT DONE | `FINAL_DEPENDENCY_LICENSE_SBOM_PACKET.md` |
| RR-04 | Secrets, key rotation, and environment inventory | Production configuration must prove no secret leakage, rotation path, and environment-specific separation | PARTIAL / NOT VERIFIED | `FINAL_SECRETS_ENVIRONMENT_PACKET.md` |
| RR-05 | Browser/device compatibility | Role journeys must work in supported browsers and common desktop/tablet/mobile contexts | NOT DONE | `FINAL_BROWSER_DEVICE_COMPATIBILITY_PACKET.md` |
| RR-06 | Accessibility beyond build checks | A11y cannot rely only on build success; core role journeys need accessibility proof and exception tracking | NOT DONE | `FINAL_ACCESSIBILITY_PACKET.md` |
| RR-07 | Payment/security compliance boundaries | Billing/payment flows need explicit PCI-scope posture, provider-tokenization assumptions, and no-card-data guarantees | NOT DONE | `FINAL_PAYMENT_SECURITY_SCOPE_PACKET.md` |
| RR-08 | Data migration and import rollback | Customer onboarding depends on safe imports, validation, rollback, duplicate handling, and audit logs | NOT DONE | `FINAL_DATA_MIGRATION_IMPORT_PACKET.md` |
| RR-09 | Multi-tenant provisioning and offboarding | Production requires tenant creation, configuration, suspension, archival, and offboarding controls | NOT DONE | `FINAL_TENANT_LIFECYCLE_PACKET.md` |
| RR-10 | Email/SMS/notification deliverability | Admissions, billing, aid, attendance, and CRM workflows depend on reliable outbound communications and failure handling | NOT DONE | `FINAL_NOTIFICATION_DELIVERABILITY_PACKET.md` |
| RR-11 | Reporting/export privacy | Exports and reports can leak sensitive data if role, tenant, and field-level controls are incomplete | NOT DONE | `FINAL_REPORTING_EXPORT_PRIVACY_PACKET.md` |
| RR-12 | Data retention, legal hold, and purge execution | Policy text is insufficient unless retention and purge execution paths are proven or explicitly scoped | NOT DONE | `FINAL_RETENTION_PURGE_PACKET.md` |
| RR-13 | Backup restore and recovery time proof | Backup policy must include actual restore proof and expected recovery behavior | NOT DONE | `FINAL_BACKUP_RESTORE_PROOF.md` |
| RR-14 | Rollback and release recovery | Production release needs rollback/redeploy procedure and failure-mode testing | NOT DONE | `FINAL_RELEASE_ROLLBACK_PACKET.md` |
| RR-15 | Microsoft 365 and Teams operational readiness | MS365 strategy requires Entra/Graph/Teams readiness proof, admin configuration, failure handling, and tenant mapping | NOT DONE | `FINAL_M365_TEAMS_READINESS_PACKET.md` |
| RR-16 | Buyer/customer-facing truth control | Sales/demo/investor/customer materials must match the actual release authority and avoid overclaiming | NOT DONE | `FINAL_CUSTOMER_TRUTH_ALIGNMENT_PACKET.md` |
| RR-17 | Support permissions and staff impersonation | Support access must be scoped, audited, time-bound where possible, and customer-understandable | NOT DONE | `FINAL_SUPPORT_ACCESS_PACKET.md` |
| RR-18 | Sandbox-to-production separation | Sandbox data, login options, demo resets, and sample dashboards must not be confused with production behavior | NOT DONE | `FINAL_SANDBOX_PRODUCTION_SEPARATION_PACKET.md` |
| RR-19 | Disaster and degraded-mode behavior | Core workflows need documented degraded behavior for external provider outage, database issue, auth issue, or MS365 issue | NOT DONE | `FINAL_DEGRADED_MODE_PACKET.md` |
| RR-20 | End-to-end critical path ownership | Each golden path needs a named owner, evidence owner, and final signoff owner | NOT DONE | `FINAL_CRITICAL_PATH_OWNERSHIP_MATRIX.md` |

## Integration with existing sprint plan

These risks extend, not replace, the existing sprint controls:

- `SCORE_GAP_CLOSURE_MAP_20260530.md`
- `SANDBOX_READY_GATE_20260601.md`
- `PRODUCTION_RELEASE_ROADMAP_20260701.md`
- `COMPLIANCE_CUSTOMER_READINESS_AUDIT_20260530.md`
- `FINAL_SIGNOFF_TEMPLATE_20260530.md`

## Production release rule

If any residual risk remains NOT DONE and production-relevant, unrestricted production release remains NO-GO.

## Sandbox rule

For sandbox readiness, each residual risk must be either:

- not applicable to sandbox,
- explicitly limited in sandbox documentation,
- or proven safe for sandbox use.

## Current conclusion

Residual risk closure is NOT DONE. These rows must be assigned into P0/P1/P2/P3 execution before final release signoff.
