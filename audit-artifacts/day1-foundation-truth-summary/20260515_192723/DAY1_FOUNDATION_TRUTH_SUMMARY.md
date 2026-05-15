# Day 1 Foundation Truth Summary

Generated: 2026-05-15T19:27:23Z
Branch: chore/day1-foundation-truth-dev-setup-core-shadowed
Head (pre-commit): 190ff8678c4f85a0196cfe5b23287a75347ad1ce

## Scope
- Created canonical docs/engineering/DEV_SETUP.md
- Added README getting-started link
- Marked older setup docs as subordinate to DEV_SETUP.md
- Moved core_shadowed to archive/non_importable/core_shadowed
- Added Day 1 verification script at scripts/verification/verify_day1_foundation_truth.sh

## Verification

### Required files
- PASS: README.md
- PASS: docs/engineering/DEV_SETUP.md
- PASS: docs/BUILD_RULES.md
- PASS: docs/engineering/ONBOARDING_GUIDE.md
- PASS: docs/canons/CROWN_DEV_CANON.md
- PASS: archive/non_importable/core_shadowed/ARCHIVE_NOTICE.md
- PASS: scripts/verification/verify_day1_foundation_truth.sh
- PASS: .github/pr-body-day1-foundation-truth.md

### Root core shadow check
- PASS: no root-level core directory

### core_shadowed location
- PASS: core_shadowed not at repo root
- PASS: core_shadowed archived under archive/non_importable

### Canonical setup links (DEV_SETUP.md references)
README.md:7:**For developers:** See [CROWN Developer Setup](docs/engineering/DEV_SETUP.md) for the canonical local development guide.
docs/BUILD_RULES.md:11:**Developer setup authority**: See [docs/engineering/DEV_SETUP.md](engineering/DEV_SETUP.md)
docs/BUILD_RULES.md:13:If this document contains older local paths, older virtual-environment locations, or duplicated startup commands that conflict with `DEV_SETUP.md`, the `DEV_SETUP.md` guide controls.
docs/engineering/ONBOARDING_GUIDE.md:9:**Developer setup authority**: See [DEV_SETUP.md](DEV_SETUP.md)
docs/engineering/ONBOARDING_GUIDE.md:11:If this document contains older setup commands or local paths that conflict with `DEV_SETUP.md`, the `DEV_SETUP.md` guide controls.
docs/canons/CROWN_DEV_CANON.md:10:**Developer setup authority**: See [../engineering/DEV_SETUP.md](../engineering/DEV_SETUP.md)
docs/canons/CROWN_DEV_CANON.md:12:If this document contains older setup commands or paths that conflict with `DEV_SETUP.md`, the `DEV_SETUP.md` guide controls.

### Machine-local path scan (docs + README only, max 50 hits)
docs/audit/DEEP_DIVE_ANALYSIS.md:112:C:\Users\JMega\OneDrive\Desktop\Crown2026\
docs/audit/DEEP_DIVE_ANALYSIS.md:145:Copy-Item -Recurse "C:\Users\JMega\OneDrive\Desktop\Crown2026" "C:\Development\Crown2026"
docs/audit/DJANGO_CRASHES_ANALYSIS.md:95:C:\Users\JMega\OneDrive\Desktop\Crown2026\backend\db.sqlite3
docs/audit/DJANGO_CRASHES_ANALYSIS.md:375:C:\Users\JMega\OneDrive\Desktop\Crown2026\backend\venv\
docs/audit/DJANGO_CRASHES_ANALYSIS.md:590:C:\Users\JMega\OneDrive\Desktop\Crown2026\  ← OneDrive monitors this
docs/audit/DJANGO_CRASHES_ANALYSIS.md:594:C:\Users\JMega\Documents\crown2026\         ← Local storage, no sync
docs/audit/DJANGO_CRASHES_ANALYSIS.md:607:Copy-Item "C:\Users\JMega\OneDrive\Desktop\Crown2026" `
docs/audit/DJANGO_CRASHES_ANALYSIS.md:608:          "C:\Users\JMega\Development\Crown2026" -Recurse
docs/audit/DJANGO_CRASHES_ANALYSIS.md:611:Remove-Item "C:\Users\JMega\OneDrive\Desktop\Crown2026\backend\venv" -Recurse -Force
docs/audit/DJANGO_CRASHES_ANALYSIS.md:614:cd C:\Users\JMega\Development\Crown2026\backend
docs/audit/DJANGO_CRASHES_ANALYSIS.md:982:- [ ] Copy to local storage: `C:\Users\JMega\Development\Crown2026`
docs/audit/reports/AUDIT_REPORT_20260222_145853_7e3dc059.md:189:Package.json path confirmed: `C:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\package.json`
docs/release/evidence/live-pack/20260411_075919/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/evidence/live-pack/20260411_044809/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/evidence/live-pack/20260411_045453/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/evidence/live-pack/20260411_081446/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/evidence/live-pack/20260411_075358/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/evidence/live-pack/20260411_075803/docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/release/live-audit/phase1/phase1_live_repo_baseline.md:7:- Repo root: C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr
docs/spine/DAILY_LOG_2026-02-02.md:54:& "C:\Users\JMega\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000  # Failed silently
docs/spine/DAILY_LOG_2026-02-02.md:109:cd C:\Users\JMega\OneDrive\Desktop\Crown2026
docs/ops/README_GOLDEN_PATH.md:76:cd C:\Users\JMega\OneDrive\Desktop\Crown2026
docs/ops/README_GOLDEN_PATH.md:91:cd C:\Users\JMega\OneDrive\Desktop\Crown2026
docs/ops/README_GOLDEN_PATH.md:126:{"path":"C:/Users/JMega/logs.zip"}
docs/ops/README_GOLDEN_PATH.md:136:{"path":"C:\Users\JMega\logs.zip"}
docs/ops/README_GOLDEN_PATH.md:220:cd C:\Users\JMega\OneDrive\Desktop\Crown2026
docs/BREAK_GLASS_BRANCH_PROTECTION.md:18:cd "C:\Users\JMega\OneDrive\Desktop\Crown2026"

### Changed files (working tree vs origin/main)
