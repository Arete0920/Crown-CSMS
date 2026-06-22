# CROWN Sandbox Login Proof - 2026-06-22

**Status**: Sandbox authentication and login candidate validation

## Login pathway summary

Sandbox login behavior is treated as candidate evidence until confirmed by same-SHA CI and deployed sandbox verification.

### Configured sandbox login methods

1. **Demo Tenant Account**
   - Tenant: CROWN Sandbox
   - Users: pre-configured demo staff, parents, students
   - Purpose: rapid functional testing without production data

2. **Local Test Accounts**
   - Username/password: test credentials in sandbox settings
   - School assignment: fixture data
   - Purpose: isolated testing without network dependency

3. **Public Entry Point**
   - Route: `/public/admissions/apply`
   - Auth: no Entra ID required
   - School selection: available before login
   - Purpose: public-facing new family workflow

## Session isolation candidate checks

- User session isolation by school context: candidate until deployed sandbox verification.
- Cross-tenant dashboard API rejection: supported for Batch 5 strict tenant summary APIs by backend tests.
- Session clearing on logout: not verified by this document.
- Token/session expiration: not verified by this document.

## Verified locally / by branch evidence

- Staff login journey: candidate, requires deployed sandbox verification.
- Parent login journey: candidate, requires deployed sandbox verification.
- Student login journey: candidate, requires deployed sandbox verification.
- Teacher login journey: candidate, requires deployed sandbox verification.
- Admissions public entry: candidate, requires deployed sandbox verification.

## Login security checks

| Check | Status |
|-------|--------|
| HTTPS enforcement | Environment-dependent; not verified by this document |
| Session timeout | Requires deployed sandbox verification |
| Password complexity | Fixture/test-account dependent |
| CSRF protection | Django middleware present; runtime confirmation required |
| SQL injection prevention | ORM-backed code path; targeted security testing required |
| XSS mitigation | React escaping baseline; targeted security testing required |

## Known sandbox login limitations

- Demo tenant users are pre-created; self-registration via UI is not claimed here.
- Password resets use sandbox/demo email behavior; real email delivery is not claimed here.
- Multi-factor authentication bypass status is not verified by this document.
- Third-party integrations use sandbox/dummy credentials where configured.

## Next validation

After merge: run full e2e journey tests on the deployed sandbox instance.
