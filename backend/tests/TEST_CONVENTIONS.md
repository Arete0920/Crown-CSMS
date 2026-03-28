# Backend Test Conventions

## Tenant enforcement is a first-order contract

Tenant resolution is enforced in middleware for API paths.
API tests must satisfy tenant context explicitly, or they will fail early by design before permission/view logic executes.

Required test behavior:

1. For API requests that are unauthenticated but expected to reach auth checks (401/403), include `HTTP_X_SCHOOL_ID` in the request.
2. For authenticated API tests, ensure test users have `school` populated when using `force_authenticate` or session login paths.
3. For tests expecting tenant errors, assert the explicit tenant failure contract (`missing_tenant`, `invalid_tenant_header`, etc.) rather than generic auth failures.
4. Only exempt endpoints listed by tenant middleware policy should omit tenant context.

## Practical patterns

### Unauthenticated API request

Use:

```python
resp = self.client.get("/api/some-endpoint/", HTTP_X_SCHOOL_ID=str(self.school.id))
self.assertEqual(resp.status_code, 401)
```

### Authenticated API request

Use:

```python
self.user = UserAccount.objects.create_user(..., school=self.school)
self.client.force_authenticate(user=self.user)
resp = self.client.get("/api/some-endpoint/")
```

## Why this is required

Tenant middleware now executes as part of the core API contract.
Tests that omit tenant context can fail with 400 before hitting endpoint permissions/logic, which masks true intent of auth/business assertions.
