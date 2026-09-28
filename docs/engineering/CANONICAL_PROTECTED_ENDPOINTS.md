# Canonical Protected Endpoints

These are the only approved production protected-endpoint proof routes for CROWN.

## Protected endpoints

- `/api/v1/admissions/summary/`
- `/api/v1/finance/metrics/`
- `/api/v1/board/dashboard/`

## Health endpoint

- `/health`

## Required proof matrix

For each protected endpoint, run:

1. no auth
2. valid auth without tenant header
3. valid auth with wrong tenant
4. valid auth with correct tenant

## Certification rule

Do not certify production until the following all match exactly:

1. GitHub workflow SHA
2. Docker image tag SHA
3. Azure configured container tag SHA
4. Live `/health` `build_sha`

## Exclusions

- Do not use stale routes such as `/api/dashboard/me`.
- Do not use legacy routes such as `/api/director/dashboard/` for production certification.
