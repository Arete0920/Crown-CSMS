## Summary

Day 1 foundation-truth cleanup.

This PR:
- creates the canonical developer setup document at `docs/engineering/DEV_SETUP.md`
- adds a README getting-started link
- marks older setup docs as non-authoritative where they conflict with `DEV_SETUP.md`
- quarantines legacy `core_shadowed` under `archive/non_importable/`
- adds a verification script for this Day 1 cleanup
- captures evidence under `audit-artifacts/day1-foundation-truth/`

## Scope

- [x] Docs authority cleanup
- [x] Legacy archived-code quarantine
- [x] Verification script
- [x] Evidence capture
- [ ] Runtime feature change
- [ ] Data model change
- [ ] Azure/deployment change
- [ ] SOLOMON change

## Why this is safe

- No production or sandbox deployment path is changed.
- No runtime module is refactored.
- No database migration is included.
- `core_shadowed` was already documented as archived and do-not-import.
- The archive move is guarded by reference scan and verification evidence.
- Rollback is a normal git revert.

## Verification

Run:

```bash
./scripts/verification/verify_day1_foundation_truth.sh
```

Optional local checks:

```bash
.venv/bin/python backend/manage.py check
cd frontend/dashboards
npm run lint
npm run build
```

## Rollback

Revert this PR. No data migration or production state change expected.

## Readiness impact

This PR improves maintainability and developer consistency.

It does not claim:

- GA readiness
- pilot approval
- compliance certification
- production release approval
- score increase by itself
