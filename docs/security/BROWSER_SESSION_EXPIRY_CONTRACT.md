# CROWN browser session expiry — interim October 2026 release contract

## Scope and decision

The standard non-sandbox dashboard login uses `POST /api/v1/auth/token/`
(SimpleJWT), whose accepted source config currently assigns a 30-minute
access-token lifetime. `LoginPage.jsx` retains access only in tab-scoped
`sessionStorage` and explicitly discards refresh credentials outside sandbox
mode. This is the interim contract: **reauthenticate when access is rejected**;
do not silently refresh, retry a write, or extend a session.

An authenticated API request returning **401** with the same still-current
bearer credential clears known browser-held token, user and school context and
navigates to `/login?reason=session-expired`. The sign-in page explains why the
user must sign in again. Explicit logout uses the same cleanup. Responses 403,
429 and 503, anonymous requests, responses from unrelated origins, stale
in-flight requests after another login, and network failures do not trigger
the expiry cleanup. Server-side role/tenant checks remain authoritative.

This 401 handler covers requests that use the canonical `authenticatedFetch`
transport; it does **not** intercept every raw `fetch`, Axios, MSAL, or
cookie-backed route in the dashboard. Existing first-party components have
some direct bearer-header implementations. Their expiry/redirect behavior
requires a route-by-route inventory and hosted role testing before a
whole-application session-continuity claim is warranted.

This browser cleanup is **not token revocation**. Existing signed access tokens
are still valid at the server until their own expiry or any server-side
revocation policy. The UI guard is not an authorization control. A failed
non-idempotent write must not be replayed without a separately reviewed
idempotency and user-intent contract. Warn users about session duration before
they begin long form submissions if necessary; preserve locally saved drafts
independently of authentication state.

## Distinct issuers and other clients

- **Dashboard SimpleJWT**: `/api/v1/auth/token/` and
  `/api/v1/auth/token/refresh/`, tracked in #350. The shared
  `jwtLogin` helper likewise does not persist a browser refresh credential.
  The accepted server rotation/blacklist code is not proof of hosted activation.
- **Legacy signed Crown JWT**: `/api/auth/login/` and
  `/api/auth/refresh/`, tracked in #372. Server-side one-use refresh logic
  is source-merged, but `CROWN_LEGACY_REFRESH_ONE_USE_ENABLED` must remain
  disabled until its separate client, schema, rollback and hosted acceptance
  gates are evidenced. Existing consuming scripts must not be mistaken for
  production browser refresh support.
- **Microsoft identity**: MSAL silent/popup access-token acquisition is
  implemented in its own client hook, with a separate identity/cookie lifecycle.
  Do not assume this is interchangeable with SimpleJWT bearer refresh.
- **Heritage sandbox**: its own session endpoint and explicit demo-mode keys
  are maintained. This source patch deliberately does not expire synthetic
  sandbox sessions through production reauthentication logic.
- **Other first-party callers**: Windows demonstration scripts, administrative
  scripts, and any deployed non-browser clients need an issuer-by-issuer audit
  and owned acceptance. Client source existence is not proof of deployed use.

## Acceptance tests and gates

Source-level regression tests for the shared client should demonstrate:

1. Matching authenticated 401 clears known browser authentication state,
   prompts sign-in, and sends exactly **one** API request (no automatic retry).
2. Even an opting-out `validateStatus` callback cannot bypass expiration
   handling; 403/429/503 and network failures do not clear credentials.
3. A delayed 401 from a prior access credential cannot clear a newer login.
4. Cross-origin responses do not inherit bearer/tenant headers or end a local
   session, and ordinary local/configured API requests still receive expected
   headers.
5. Explicit logout removes known session/local legacy credential keys while
   preserving unrelated user draft state; sandbox behavior is unchanged.
6. Shared login never stores refresh tokens for the production browser flow.

Also run existing dashboard unit/build/lint and backend authentication tests.
These are source assurances, **not hosted acceptance**. The hosted evidence
still needs an approved synthetic user on the actual deployed frontend/API,
matching source and deployment SHA, role and tenant coverage, signed-in API
success, forced expiry yielding a controlled sign-in prompt, no unauthorized
data exposure, no automatic replay, logout cleanup, and regression checks for
forbidden, rate-limited and unavailable backends. Preserve sanitized receipts
and never log bearer tokens or passwords.

For the October 29 release gate, keep both
`CROWN_SIMPLEJWT_BLACKLIST_ENABLED=false` and
`CROWN_LEGACY_REFRESH_ONE_USE_ENABLED=false` **unless separate written
operational authority and complete respective schema/client/rollback/hosted
acceptance proof exist**. The DEV migration plan showing zero pending reviewed
migrations does not establish that either enforcement flag is active.
Neither this document nor a merged frontend PR grants deployment authority.

Future continuous sessions require an explicitly approved design for secure
refresh-token custody (prefer a suitably protected server-managed session or
HttpOnly cookie contract where feasible), replacement, concurrent refresh
single-flight, replay and revoked-token behavior, bounded lifetime, tenant/role
reverification and complete mobile/desktop/browser compatibility. Do not
reintroduce `sessionStorage` refresh credentials merely to preserve UX.
