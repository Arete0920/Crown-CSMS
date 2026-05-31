# CROWN Observability and Incident Readiness — 2026-05-29

## Decision

**OBSERVABILITY / INCIDENT READINESS: NOT GREEN.**

CROWN cannot be certified pilot-ready, GA-ready, or superior without operational monitoring, incident response evidence, and production-support controls.

## Required observability controls

| Control | Requirement | Status |
|---|---|---|
| OBS-001 | Uptime/health monitoring exists for frontend, backend, database, and critical background jobs | NOT_GREEN |
| OBS-002 | Error monitoring captures backend exceptions, frontend runtime errors, failed jobs, and integration failures | NOT_GREEN |
| OBS-003 | Security monitoring detects failed login spikes, suspicious privileged access, and cross-tenant anomaly signals | NOT_GREEN |
| OBS-004 | Payment/webhook monitoring captures delivery failures, signature failures, duplicate events, and reconciliation failures | NOT_GREEN |
| OBS-005 | Email/SMS delivery monitoring captures bounces, failed sends, suppression/opt-out issues, and provider outages | NOT_GREEN |
| OBS-006 | Dashboard/API latency monitoring captures slow critical workflows | NOT_GREEN |
| OBS-007 | Backup monitoring detects failed/missed backups and stale restore points | NOT_GREEN |
| OBS-008 | Audit log monitoring detects missing/tampered critical logs where technically feasible | NOT_GREEN |
| OBS-009 | Tenant isolation monitoring treats cross-tenant exposure as critical until disproven | NOT_GREEN |
| OBS-010 | On-call/escalation process exists for pilot/production incidents | NOT_GREEN |

## Required incident response controls

| Control | Requirement | Status |
|---|---|---|
| IR-001 | Incident severity matrix exists | NOT_GREEN |
| IR-002 | Cross-tenant data exposure is severity critical | NOT_GREEN |
| IR-003 | Customer notification workflow exists | NOT_GREEN |
| IR-004 | Evidence preservation procedure exists | NOT_GREEN |
| IR-005 | Containment procedure exists | NOT_GREEN |
| IR-006 | Root-cause analysis template exists | NOT_GREEN |
| IR-007 | Post-incident corrective-action process exists | NOT_GREEN |
| IR-008 | Incident tabletop or test has been completed | NOT_GREEN |
| IR-009 | Support-access emergency/break-glass flow is logged and reviewed | NOT_GREEN |
| IR-010 | Contact roster is current for product owner, technical, security, customer, and legal/compliance contacts | NOT_GREEN |

## Required evidence output

```text
.crown-audit/observability/latest/00_SUMMARY.md
.crown-audit/observability/latest/10_monitoring_controls.csv
.crown-audit/observability/latest/20_incident_response_controls.csv
.crown-audit/observability/latest/30_tabletop_or_test.md
.crown-audit/observability/latest/99_STATUS.json
```

## Minimum pilot readiness threshold

Pilot readiness requires all of the following:

1. Current health checks are visible and actionable.
2. Critical errors notify an accountable person/team.
3. Security/tenant anomalies are triaged as critical.
4. Backup failures are detected.
5. Customer notification process is defined.
6. Incident tabletop/test is complete.
7. Support/break-glass access is auditable.

## Status

Readiness definition: **DOCUMENTED**

Operational certification: **NOT GREEN until runtime monitoring and incident-test evidence are attached.**
