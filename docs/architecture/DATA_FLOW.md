# Crown Data Flow Diagram

## Request / Response Path

```
Browser / React SPA
    │
    │  HTTPS + Authorization: Bearer <token>
    │  X-School-Id: <uuid>
    ▼
Azure App Service (crown-api-prod)
    │
    ├── TenantHeaderRequiredMiddleware   ← blocks requests missing X-School-Id
    ├── ApiExceptionMiddleware           ← normalises error envelopes
    ├── PerformanceMiddleware            ← logs SLOW_REQUEST at >1s
    ├── APIVersionMiddleware             ← injects X-API-Deprecated-After
    ├── JwtAuthMiddleware                ← validates Bearer token
    └── TenantContextMiddleware          ← resolves school from header
    │
    ▼
Django View / DRF ViewSet
    │
    ├── get_request_school_id(request)   ← tenant isolation gate
    ├── user_has_permission(user, perm)  ← RBAC check
    ▼
Service Layer (services_*.py)
    │
    ├── Atomic DB operations (PostgreSQL)
    ├── Celery task dispatch (Redis)
    └── External API calls (Stripe / Graph)
    │
    ▼
PostgreSQL (Azure DB Flexible Server)
```

## Async / Background Path

```
Django View
    │
    ├── task.delay() → Celery Broker (Redis)
    ▼
Celery Worker
    │
    ├── Service Layer
    └── PostgreSQL / External APIs
```

## External Integrations

```
Payment Processor (Stripe)
    → ledger/services_dunning.py (retry/reconciliation)

Microsoft Graph API
    → comms/tasks.py drain_outbox (email delivery)

Sentry
    → Error telemetry (prod only)

Azure Key Vault
    → Secrets loaded at startup via managed identity
```
