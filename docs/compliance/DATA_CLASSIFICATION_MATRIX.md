# DATA CLASSIFICATION MATRIX

| Classification | Examples | Access Model |
|---|---|---|
| Public Operational | calendars, announcements | broad |
| Restricted Educational | grades, attendance | RBAC |
| Financial Restricted | tuition, billing | finance-only |
| Sensitive Faith | prayer requests, spiritual_life | elevated RBAC |
| Highly Restricted | counseling/intervention | minimum necessary |

## Enforcement

- tenant-scoped queries
- deny-by-default middleware
- audit logging
- export restrictions
- role-based permissions
