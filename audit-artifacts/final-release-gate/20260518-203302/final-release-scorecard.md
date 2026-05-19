# CROWN Final Release Gate Scorecard

- Run ID: 20260518-203302
- Decision: NO-GO
- Branch: release/final-sprint-current-main-20260518-193231
- HEAD: ae6fdc274a452045fb0d487a4a6ee9a3cf6685f6
- Origin main: 273461a91e101cbd4c63314f7627a063b9c4beda
- PASS: 9
- WARN: 1
- FAIL: 9

## Gates

- **FAIL** - release branch: Final release gate must run on main. Current branch: release/final-sprint-current-main-20260518-193231
- **FAIL** - working tree clean: Working tree has uncommitted changes
- **FAIL** - main sync: HEAD ae6fdc274a452045fb0d487a4a6ee9a3cf6685f6 does not match origin/main 273461a91e101cbd4c63314f7627a063b9c4beda
- **PASS** - required file: docs/testing/crown-test-inventory.json: Present
- **PASS** - required file: scripts/testing/check-crown-test-inventory.mjs: Present
- **PASS** - required file: scripts/testing/check-crown-discovered-surface-coverage.mjs: Present
- **PASS** - required file: scripts/testing/crown-surface-discovery.mjs: Present
- **PASS** - required file: docs/KNOWN_LIMITATIONS.md: Present
- **PASS** - required file: docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md: Present
- **PASS** - required file: docs/release/README.md: Present
- **FAIL** - crown test inventory: node scripts/testing/check-crown-test-inventory.mjs exited 
- **FAIL** - crown discovered surface coverage: node scripts/testing/check-crown-discovered-surface-coverage.mjs exited 
- **FAIL** - django check: python backend/manage.py check exited 
- **FAIL** - django migrations dry run: python backend/manage.py makemigrations --check --dry-run exited 
- **FAIL** - frontend build: This command cannot be run due to the error: %1 is not a valid Win32 application.
- **FAIL** - frontend verify full: This command cannot be run due to the error: %1 is not a valid Win32 application.
- **PASS** - open PR backlog: No open PRs
- **PASS** - open issue backlog: No open issues
- **WARN** - production currentness: Skipped by -SkipProductionProbe
