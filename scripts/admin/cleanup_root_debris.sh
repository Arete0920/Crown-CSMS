#!/usr/bin/env bash

set -euo pipefail

echo "==> Removing stale operational files from repo root..."

STALE_FILES=(
  "ACTUAL_STATUS_TODAY.md"
  "BASELINE_REALITY.md"
  "BRANCH_PROTECTION.md"
  "CHECKLIST.md"
  "CHECKPOINTS.md"
  "env_check.txt"
  "ep_errors.txt"
  "ep_with_school.txt"
)

STALE_PATTERNS=(
  "AUDIT_*.md"
  "AUDIT_REPORT*.md"
)

for f in "${STALE_FILES[@]}"; do
  if [ -f "$f" ]; then
    git rm "$f"
    echo "  Removed: $f"
  else
    echo "  Not found (skipping): $f"
  fi
done

for pattern in "${STALE_PATTERNS[@]}"; do
  for f in $pattern; do
    if [ -f "$f" ]; then
      git rm "$f"
      echo "  Removed: $f"
    fi
  done
done

if git ls-files --error-unmatch artifacts/ > /dev/null 2>&1; then
  git rm -r artifacts/
  echo "  Removed: artifacts/"
fi

echo
echo "==> Done. Review with: git status"