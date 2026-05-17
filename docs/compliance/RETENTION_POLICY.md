# RETENTION POLICY

| Data Type | Retention |
|---|---|
| Admissions inquiries | 365 days |
| Student records | active enrollment + policy retention |
| Billing records | legal/financial retention period |
| Prayer requests | active + 180 days |
| Audit logs | 7 years |
| Temporary uploads | 30 days |

## Enforcement

Retention enforcement is executed through scheduled
management commands and audit logging.

## Deletion Model

- soft-delete first
- audit verification
- permanent purge after retention window
