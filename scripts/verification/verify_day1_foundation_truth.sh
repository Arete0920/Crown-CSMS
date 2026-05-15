#!/usr/bin/env bash
set -euo pipefail

repo="$(git rev-parse --show-toplevel)"
cd "$repo"

stamp="$(date +"%Y%m%d_%H%M%S")"
out="audit-artifacts/day1-foundation-truth-verify/$stamp"
mkdir -p "$out"

{
  echo "REPO=$repo"
  echo "BRANCH=$(git branch --show-current)"
  echo "HEAD=$(git rev-parse HEAD)"
} > "$out/00_context.txt"

echo "=== Git status ===" > "$out/01_git_status.txt"
git status --short >> "$out/01_git_status.txt"

echo "=== Required files ===" > "$out/02_required_files.txt"
required=(
  "docs/engineering/DEV_SETUP.md"
  "README.md"
  "docs/BUILD_RULES.md"
  "docs/engineering/ONBOARDING_GUIDE.md"
  "docs/canons/CROWN_DEV_CANON.md"
  "scripts/verification/verify_day1_foundation_truth.sh"
)

for f in "${required[@]}"; do
  if [ -f "$f" ]; then
    echo "[PASS] $f" >> "$out/02_required_files.txt"
  else
    echo "[FAIL] $f" >> "$out/02_required_files.txt"
  fi
done

echo "=== Forbidden active root core check ===" > "$out/03_root_core_check.txt"
if [ -d "core" ]; then
  echo "[FAIL] root-level core directory exists" >> "$out/03_root_core_check.txt"
else
  echo "[PASS] no root-level core directory" >> "$out/03_root_core_check.txt"
fi

echo "=== core_shadowed active-location check ===" > "$out/04_core_shadowed_check.txt"
if [ -d "core_shadowed" ]; then
  echo "[FAIL] core_shadowed still exists at repo root" >> "$out/04_core_shadowed_check.txt"
else
  echo "[PASS] core_shadowed not at repo root" >> "$out/04_core_shadowed_check.txt"
fi

if [ -d "archive/non_importable/core_shadowed" ]; then
  echo "[PASS] core_shadowed archived under archive/non_importable" >> "$out/04_core_shadowed_check.txt"
else
  echo "[FAIL] archive/non_importable/core_shadowed not found" >> "$out/04_core_shadowed_check.txt"
fi

echo "=== Canonical setup links ===" > "$out/05_canonical_setup_links.txt"
grep -RIn "DEV_SETUP.md" README.md docs/BUILD_RULES.md docs/engineering/ONBOARDING_GUIDE.md docs/canons/CROWN_DEV_CANON.md \
  >> "$out/05_canonical_setup_links.txt" || true

echo "=== Machine-local path scan: Day 1 scope docs only ===" > "$out/06_machine_path_scan.txt"
{
  grep -InE 'C:\\Users|C:/Users' \
    README.md \
    docs/BUILD_RULES.md \
    docs/engineering/DEV_SETUP.md \
    docs/engineering/ONBOARDING_GUIDE.md \
    docs/canons/CROWN_DEV_CANON.md \
    2>/dev/null || true
} | head -50 >> "$out/06_machine_path_scan.txt"

echo "=== core_shadowed external reference scan ===" > "$out/07_core_shadowed_reference_scan.txt"
find . -type f \
  ! -path "./.git/*" \
  ! -path "./archive/non_importable/core_shadowed/*" \
  ! -path "./audit-artifacts/day1-foundation-truth/*" \
  ! -path "./audit-artifacts/day1-foundation-truth-verify/*" \
  \( -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" -o -name "*.json" -o -name "*.yml" -o -name "*.yaml" \) \
  -print0 | xargs -0 grep -In "core_shadowed" >> "$out/07_core_shadowed_reference_scan.txt" || true

echo "=== Django check if local venv exists ===" > "$out/08_django_check.txt"
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python backend/manage.py check >> "$out/08_django_check.txt" 2>&1
elif [ -x "venv/bin/python" ]; then
  venv/bin/python backend/manage.py check >> "$out/08_django_check.txt" 2>&1
else
  echo "[SKIP] No repo-root .venv or venv found locally. Docs-only verification continues." >> "$out/08_django_check.txt"
fi

echo "=== Diff stat ===" > "$out/09_diff_stat.txt"
git diff --stat >> "$out/09_diff_stat.txt"

echo "Verification written to $out"
