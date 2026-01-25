# Ops Log

Human notes for operational events/decisions (not tickets, not runbooks).

---

## 2026-01-25 — Exports spine complete through 0094
- Exports spine complete through 0094 (statements + detail), tagged and merged.

## 2026-01-24 — Production deploy confirmed green
- GitHub Actions run: 21324588467 (success)
- Deployed commit: b991e1f0ab7376d7708b74914c2d696711eb9c73
- Health endpoints: `/health/` and `/api/health/` returned 200 with `build_sha` `b991e1f`
- Tag pushed: `prod-green-20260124-2022`
- `AZURE_CREDENTIALS` rotated and re-set via stdin on 2026-01-24 (no further rotations unless security-driven)

## 2026-01-24 — Discipline rule: stop workflow thrash
- `deploy-prod.yml` changes require a ticket + scoped intent (no more “poke until green”).
- Secrets/credentials rotation is security-driven only (document date + reason here).
- Stabilization work branches off the prod-green tag; main stays boring.
