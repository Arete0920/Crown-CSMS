# CROWN Demo and Sandbox Mode Policy

## 1. Purpose

CROWN distinguishes two controlled non-production capabilities:

- **Backend demo mode** supports seeded-data demonstrations and non-production operational safeguards.
- **Heritage sandbox mode** provides an evaluator-facing, passwordless preview of Heritage Christian Academy.

Neither capability is a silent fallback data layer. API and session failures must remain visible.

## 2. Backend demo mode

| Item | Contract |
|------|----------|
| Setting | `settings.CROWN_DEMO_MODE` |
| Env variable | `CROWN_DEMO_MODE=true` |
| Default | `False` |
| Production guard | `_assert_not_prod_true("CROWN_DEMO_MODE", CROWN_DEMO_MODE)` |
| Write protection | Demo-mode middleware may block mutating HTTP methods |

Backend code must read the parsed Django setting rather than directly interpreting the environment variable.

## 3. Heritage sandbox entry

The Heritage sandbox is not a credential login flow.

- Evaluators select a permitted role.
- The frontend creates a temporary role-scoped session through `POST /api/v1/sandbox/session/`.
- An approved invite is required unless a controlled open-session window is explicitly enabled.
- Heritage Christian Academy is the only exposed sandbox school.
- The frontend must not request, display, prefill, copy, or store a sandbox username or password.
- The sandbox flow must not call `/api/v1/auth/token/`.
- `VITE_DEMO_USER`, `VITE_DEMO_PASS`, and `VITE_DEMO_AUTO_LOGIN` are obsolete and prohibited for sandbox entry.

Normal authentication for real production users remains unchanged.

## 4. Prohibited silent fallback

Dashboard request failures must produce an explicit error. Catch blocks may not silently replace failed live data with static sample data.

```jsx
fetchData()
  .then(setData)
  .catch((error) => {
    setError(`Dashboard unavailable - API error: ${error.message}`);
  });
```

## 5. Permitted controlled uses

| Component | Permitted use |
|-----------|---------------|
| Backend demo-mode middleware | Non-production write protection |
| Localhost-only developer token endpoint | Developer tooling, separate from sandbox entry |
| Health endpoint demo-mode indicator | Operational visibility |
| Explicit deterministic seeded responses | Only where documented and never as a hidden fallback |
| Heritage sandbox session endpoint | Passwordless evaluator session provisioning |
| Credential auto-login wrappers or public credential manifests | Prohibited |

## 6. Production boundary

`CROWN_DEMO_MODE=true` must remain rejected when the application is configured as production. The Heritage sandbox exception is separately bounded by its school, invite/session, role, and tenant checks and must not weaken production tenant authentication.

## 7. Change log

| Date | Change |
|------|--------|
| 2026-02-25 | Initial demo-mode policy and removal of silent dashboard fallback behavior |
| 2026-08-05 | Reconciled policy with the passwordless, Heritage-only sandbox session contract; retired credential auto-login configuration and artifacts |
