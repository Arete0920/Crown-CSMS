# Tenant & Privacy Canon (Crown)

## 1. Tenant context is mandatory
All tenant-scoped requests MUST include school context.

**Canonical tenant key:** `X-School-Id` (UUID)  
**Legacy alias (deprecated):** `X-Crown-School-Id` (supported for backward compatibility)

If tenant context is missing or invalid:
- API MUST return **400 Bad Request**
- Response MUST NOT reveal existence of tenant data

## 2. Single entry point
All code MUST obtain tenant context ONLY via:

- `get_request_school_id(request) -> UUID`

No other direct header/cookie parsing is permitted outside this helper.

## 3. Privacy rule: do not leak existence
For non-staff users:
- Cross-tenant access MUST return **404 Not Found** (not 403)

Rationale: returning 403 can confirm an object exists.

## 4. Ownership rules
A request is allowed only if:
- The user is authorized for the tenant, AND
- The object is in the same tenant

Tenant mismatch MUST behave like "not found" for non-staff.

## 5. Enforcement points
Tenant context must be enforced at:
- View permission checks (entry)
- Queryset filtering (data layer)
- Any export/report endpoints (CSV/PDF)

## 6. Tests are the contract
The following tests MUST exist and pass:

- Missing tenant context → 400
- Wrong tenant context → 404 (non-staff)
- Correct tenant context → 200
- Querysets never return cross-tenant rows
