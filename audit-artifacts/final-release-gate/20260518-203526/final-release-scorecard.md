# CROWN Final Release Gate Scorecard

- Run ID: 20260518-203526
- Decision: NO-GO
- Branch: release/final-sprint-current-main-20260518-193231
- HEAD: cba629a69134231b75370f313a5c802a78378ee5
- Origin main: 273461a91e101cbd4c63314f7627a063b9c4beda
- PASS: 15
- WARN: 1
- FAIL: 3

## Gates

- **FAIL** - release branch: Final release gate must run on main. Current branch: release/final-sprint-current-main-20260518-193231
- **FAIL** - working tree clean: Working tree has uncommitted changes
- **FAIL** - main sync: HEAD cba629a69134231b75370f313a5c802a78378ee5 does not match origin/main 273461a91e101cbd4c63314f7627a063b9c4beda
- **PASS** - required file: docs/testing/crown-test-inventory.json: Present
- **PASS** - required file: scripts/testing/check-crown-test-inventory.mjs: Present
- **PASS** - required file: scripts/testing/check-crown-discovered-surface-coverage.mjs: Present
- **PASS** - required file: scripts/testing/crown-surface-discovery.mjs: Present
- **PASS** - required file: docs/KNOWN_LIMITATIONS.md: Present
- **PASS** - required file: docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md: Present
- **PASS** - required file: docs/release/README.md: Present
- **PASS** - crown test inventory: node scripts/testing/check-crown-test-inventory.mjs exited 0
- **PASS** - crown discovered surface coverage: node scripts/testing/check-crown-discovered-surface-coverage.mjs exited 0
- **PASS** - django check: python backend/manage.py check exited 0
- **PASS** - django migrations dry run: python backend/manage.py makemigrations --check --dry-run exited 0
- **PASS** - frontend build: npm --prefix frontend/dashboards run build exited 0
- **PASS** - frontend verify full: npm --prefix frontend/dashboards run verify:full exited 0
- **PASS** - open PR backlog: No open PRs
- **PASS** - open issue backlog: No open issues
- **WARN** - production currentness: Skipped by -SkipProductionProbe
