# Recovery Quicksheet

**Rule:** If something fails twice, stop and revert.

## Failure Categories
- **BOOT**: server won’t start, migrations fail, settings crash
- **AUTH**: token/login fails
- **TENANT**: X-School-Id missing/ignored, data leakage risk
- **SEED**: demo data missing/duplicated, resets fail
- **CONTRACT**: frontend expects fields that backend doesn’t provide (or vice versa)
## Seed Dependencies (CRITICAL)
- **Gradebook demo data** requires academics/sections/enrollments seeded first
  - Run `seed_academics_readonly.py` or equivalent to create sections + enrollments
  - Then `python manage.py seed_gradebook_demo --school-id <UUID>` populates GradeEntry across all enrolled sections
  - Verify via API: `/api/v1/gradebook/sections/{section_id}/grades/` should return assignments + student scores
  - Seed is idempotent: re-running updates existing records (no data explosion)
## First Response Checklist
1. Identify category (BOOT/AUTH/TENANT/SEED/CONTRACT)
2. Reproduce once
3. Make ONE change
4. Re-test
5. If still failing: revert and stop

## Where the truth lives
- `BASELINE_REALITY.md`
- `docs/release/BUYER_POSITIONING_NOTES.md`
- `docs/spine/README.md`
- `docs/spine/DAILY_EXECUTION_CHECKLIST.md`
