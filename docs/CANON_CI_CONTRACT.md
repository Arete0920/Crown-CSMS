# Crown CI Contract (Canon)

## Non-negotiables
- No direct pushes to main
- Workflows must fail-fast on missing env
- All services must be waited-ready (health checks) before tests
- Playwright proofs may not depend on browser storage keys for auth

## Ports
- API: http://127.0.0.1:8000
- UI:  http://127.0.0.1:3000

## Required Secrets
- CROWN_DEMO_PASSWORD

## Proof Definition
- proof-gradebook is green only if:
  - backend migrate + seed succeed
  - /health returns 200
  - UI responds on :3000
  - API proof test passes with Authorization + X-School-Id

## Auth Contract
- Tests capture token from login response (JSON or cookies), never sessionStorage
- Login endpoint regex: `/\/api\/.*(login|token|jwt)/i`
- Token field names (in order): `access`, `access_token`, `token`, `jwt`

## Service Readiness
- API: Poll `http://127.0.0.1:8000/health/` or `http://127.0.0.1:8000/` for 60s max, 1s interval
- UI: Poll `http://127.0.0.1:3000/` for 60s max, 1s interval
- Fail-fast if service never becomes ready

## Workflow Guardrails
Every CI workflow MUST:
1. Print versions (Node, Python, Pip) at start
2. Validate required env vars exist before use
3. Wait-for-ready health checks before test execution
4. Print endpoint receipts (VITE_API_BASE_URL, API_BASE_URL, CROWN_UI_URL)

## Seed Contract
- `golden_path_bootstrap --force --school-id <uuid>` creates:
  - School (deterministic UUID)
  - Admin user (username="admin", password=$CROWN_DEMO_PASSWORD)
  - Financial aid sample data
- `seed_demo_school --students <N>` creates:
  - Director users (head@crown-demo.local, finance@crown-demo.local, etc., password="demo1234")
  - Sections with deterministic UUIDs
  - Students and enrollments

## Breaking Changes
Any change that modifies:
- Workflow env vars
- Health check endpoints
- Token extraction logic
- Seed command arguments

...REQUIRES update to this canon file + explicit PR note.
