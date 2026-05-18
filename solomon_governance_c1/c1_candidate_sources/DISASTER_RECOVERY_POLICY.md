# Crown2026 — Disaster Recovery Policy

**Version:** 1.0
**Effective:** 2026-02-28
**Owner:** Engineering Leadership

---

## Recovery Objectives

| Objective | Target |
|-----------|--------|
| RTO (Recovery Time Objective) | **4 hours** |
| RPO (Recovery Point Objective) | **1 hour** |

---

## Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Incremental | Hourly | 7 days |
| Full | Nightly (02:00 UTC) | 30 days |
| Manual pre-deploy | On every `deploy-prod.yml` run | 30 days |

Backups are stored in Azure Blob Storage (`crown-backups` container, GRS redundancy).

---

## Restore Procedure

1. Identify recovery point from Azure Backup vault or Postgres PITR.
2. Create a temporary restore target database:
   ```
   createdb restore_test_<timestamp>
   ```
3. Run `pg_restore` against the target:
   ```
   pg_restore --dbname restore_test_<timestamp> --no-owner /backups/latest.dump
   ```
4. Run smoke tests against restored DB (health endpoint + key data consistency).
5. If validation passes, promote to production using Azure PITR switchover or manual import.
6. Update `prod-deploy-<date>` tag after successful cutover.

Automation: `python manage.py verify_backup_restore`

---

## Restore Test Schedule

| Cadence | Owner | Evidence |
|---------|-------|----------|
| Quarterly | Engineering Lead | Result logged in `audit_out.txt` + PR comment |

---

## Incident Escalation

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| P0 (full outage) | 30 min | On-call → CTO |
| P1 (partial outage) | 2 hours | On-call |
| P2 (degraded) | 4 hours | Engineering |

---

## Status Page

Public uptime status: required before GA launch.
Provider: Atlassian Statuspage or BetterStack (TBD — Phase 5).

---

## Settings Reference

The following `settings.py` constants govern DR behaviour:

```python
CROWN_RTO_HOURS = 4
CROWN_RPO_HOURS = 1
CROWN_BACKUP_BUCKET = "crown-backups"
CROWN_BACKUP_RETENTION_DAYS = 30
```
