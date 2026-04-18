MERGE RULES

1. If a PR overlaps any of:
   - .github/workflows/*
   - scripts/release/*
   - backend/*/api*.py
   - backend/*/views.py
   - backend/*/urls.py
   - frontend/dashboards/*
   - docs/release/*
   it is NOT merged directly.

2. Direct merge allowed only if overlap count = 0.

3. If overlap exists:
   - review the PR
   - extract only specific files or commits
   - cherry-pick only clean, non-conflicting work
   - otherwise close/supersede the PR

4. audit/pr-overlap-reconcile remains the canonical recovery branch until release verification is rerun green.
