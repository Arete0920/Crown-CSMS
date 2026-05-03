#!/usr/bin/env bash
set -u
set -o pipefail

# ==========================================================
# CROWN FINAL PRODUCTION RELEASE PROOF PACKET - CODESPACE
# Produces:
#   audit-artifacts/final-production-release/<timestamp>/
#
# Final GO rule:
#   PASS = TOTAL
#   FAIL = 0
#   REVIEW = 0
# ==========================================================

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="audit-artifacts/final-production-release/${STAMP}"
mkdir -p "$OUT"

GATE_CSV="$OUT/GATE_RESULTS.csv"
SUMMARY="$OUT/SUMMARY.md"
DECISION="$OUT/00_FINAL_DECISION.md"
INTEGRITY_SCHOOL_ID="${INTEGRITY_SCHOOL_ID:-${CROWN_PACKET_SCHOOL_ID:-}}"
DASHBOARD_KPI_MATRIX_SOURCE="${DASHBOARD_KPI_MATRIX_SOURCE:-}"
SANDBOX_SMOKE_MATRIX_SOURCE="${SANDBOX_SMOKE_MATRIX_SOURCE:-}"

echo "Gate,Status,Evidence,Notes" > "$GATE_CSV"

add_gate() {
  local gate="$1"
  local status="$2"
  local evidence="$3"
  local notes="$4"

  gate="${gate//\"/\"\"}"
  status="${status//\"/\"\"}"
  evidence="${evidence//\"/\"\"}"
  notes="${notes//\"/\"\"}"

  printf '"%s","%s","%s","%s"\n' "$gate" "$status" "$evidence" "$notes" >> "$GATE_CSV"
}

run_capture() {
  local name="$1"
  local outfile="$2"
  local required="$3"
  shift 3

  local path="$OUT/$outfile"

  {
    echo "=== $name ==="
    echo "Timestamp: $(date -Iseconds)"
    echo "Working directory: $(pwd)"
    echo "Command: $*"
    echo ""
  } > "$path"

  if "$@" >> "$path" 2>&1; then
    add_gate "$name" "PASS" "$outfile" "Command completed."
  else
    if [ "$required" = "required" ]; then
      add_gate "$name" "FAIL" "$outfile" "Required command failed."
    else
      add_gate "$name" "REVIEW" "$outfile" "Command failed or needs review."
    fi
  fi
}

section_file() {
  local file="$1"
  local title="$2"
  {
    echo ""
    echo "============================================================"
    echo "$title"
    echo "============================================================"
    echo ""
  } >> "$file"
}

evaluate_matrix_gate() {
  local gate_name="$1"
  local file_name="$2"
  local pending_note="$3"
  local path="$OUT/$file_name"

  if awk -F, 'NR>1 && $3 == "FAIL" {found=1} END {exit found ? 0 : 1}' "$path"; then
    add_gate "$gate_name" "FAIL" "$file_name" "Matrix contains FAIL rows."
  elif awk -F, 'NR>1 && $3 == "REVIEW" {found=1} END {exit found ? 0 : 1}' "$path"; then
    add_gate "$gate_name" "REVIEW" "$file_name" "$pending_note"
  else
    add_gate "$gate_name" "PASS" "$file_name" "Matrix contains only PASS rows."
  fi
}

echo ""
echo "============================================================"
echo "CROWN FINAL PRODUCTION RELEASE PROOF PACKET"
echo "============================================================"
echo "Output folder: $OUT"
echo ""

# ==========================================================
# 0. BASIC TOOLING
# ==========================================================
run_capture "Tooling versions" "00_TOOLING_VERSIONS.txt" required bash -lc '
  echo "--- git ---"
  git --version || true
  echo "--- gh ---"
  gh --version || true
  echo "--- python ---"
  python --version || true
  echo "--- pip ---"
  python -m pip --version || true
  echo "--- node ---"
  node --version || true
  echo "--- npm ---"
  npm --version || true
  echo "--- az ---"
  az version || true
'

# ==========================================================
# 1. REPO IDENTITY / CLEAN STATE
# ==========================================================
run_capture "Repo identity" "01_REPO_IDENTITY.txt" required bash -lc '
  echo "--- remote ---"
  git remote -v
  echo ""
  echo "--- branch ---"
  git branch --show-current
  echo ""
  echo "--- head sha ---"
  git rev-parse HEAD
  echo ""
  echo "--- status short ---"
  git status --short
  echo ""
  echo "--- status branch ---"
  git status -sb
  echo ""
  echo "--- recent commits ---"
  git log --oneline -15
'

HEAD_SHA="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN)"
DIRTY="$(git status --short 2>/dev/null || true)"

if [ "$BRANCH" = "main" ]; then
  add_gate "Main branch selected" "PASS" "01_REPO_IDENTITY.txt" "Current branch is main."
else
  add_gate "Main branch selected" "FAIL" "01_REPO_IDENTITY.txt" "Current branch is $BRANCH, not main."
fi

if [ -z "$DIRTY" ]; then
  add_gate "Clean worktree" "PASS" "01_REPO_IDENTITY.txt" "No uncommitted files."
else
  add_gate "Clean worktree" "FAIL" "01_REPO_IDENTITY.txt" "Uncommitted files exist."
fi

run_capture "Main synced with origin" "01_MAIN_SYNC_PROOF.txt" required bash -lc '
  git fetch origin main
  LOCAL="$(git rev-parse HEAD)"
  REMOTE="$(git rev-parse origin/main)"
  echo "LOCAL=$LOCAL"
  echo "REMOTE=$REMOTE"
  test "$LOCAL" = "$REMOTE"
'

# ==========================================================
# 2. GITHUB QUEUE / RULESET / ACTIONS PROOF
# ==========================================================
run_capture "GitHub auth status" "02_GH_AUTH_STATUS.txt" required gh auth status
run_capture "Open PR proof" "03_OPEN_PR_PROOF.json" required \
  gh pr list --state open --json number,title,headRefName,baseRefName,mergeStateStatus,isDraft,url
run_capture "Open issue proof" "04_OPEN_ISSUE_PROOF.json" required \
  gh issue list --state open --json number,title,url,labels,assignees
run_capture "Recent Actions proof" "05_RECENT_ACTIONS_PROOF.json" required \
  gh run list --limit 50 --json databaseId,workflowName,headBranch,headSha,status,conclusion,createdAt,updatedAt,url
run_capture "Ruleset proof" "06_RULESETS_PROOF.json" required \
  gh api repos/:owner/:repo/rulesets --paginate
run_capture "Branch protection proof" "07_BRANCH_PROTECTION_PROOF.json" review \
  gh api repos/:owner/:repo/branches/main/protection
run_capture "CODEOWNERS proof" "08_CODEOWNERS_PROOF.txt" required bash -lc '
  test -f CODEOWNERS && cat CODEOWNERS || test -f .github/CODEOWNERS && cat .github/CODEOWNERS
'
run_capture "Workflow list proof" "09_WORKFLOW_LIST.txt" required bash -lc '
  find .github/workflows -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" \) | sort
'

# ==========================================================
# 3. BACKEND PROOF
# ==========================================================
if [ -f "backend/requirements.txt" ]; then
  run_capture "Backend dependency install" "10_BACKEND_DEP_INSTALL.txt" required \
    python -m pip install -r backend/requirements.txt
else
  add_gate "Backend dependency install" "FAIL" "10_BACKEND_DEP_INSTALL.txt" "backend/requirements.txt not found."
fi

if [ -f "backend/manage.py" ]; then
  run_capture "Backend Django check" "11_BACKEND_DJANGO_CHECK.txt" required \
    python backend/manage.py check
  run_capture "Backend migration status" "12_BACKEND_MIGRATIONS.txt" required \
    python backend/manage.py showmigrations
  run_capture "Backend deploy check" "13_BACKEND_DEPLOY_CHECK.txt" required \
    python backend/manage.py check --deploy
  run_capture "Backend tests" "14_BACKEND_TESTS.txt" required \
    python backend/manage.py test
else
  add_gate "Backend manage.py exists" "FAIL" "11_BACKEND_DJANGO_CHECK.txt" "backend/manage.py not found."
  add_gate "Backend migration status" "FAIL" "12_BACKEND_MIGRATIONS.txt" "backend/manage.py not found."
  add_gate "Backend deploy check" "FAIL" "13_BACKEND_DEPLOY_CHECK.txt" "backend/manage.py not found."
  add_gate "Backend tests" "FAIL" "14_BACKEND_TESTS.txt" "backend/manage.py not found."
fi

# ==========================================================
# 4. FRONTEND PROOF
# ==========================================================
if [ -d "frontend/dashboards" ]; then
  run_capture "Frontend package files" "20_FRONTEND_PACKAGE_FILES.txt" required bash -lc '
    cd frontend/dashboards
    pwd
    ls -la
    test -f package.json
  '
  run_capture "Frontend install" "21_FRONTEND_INSTALL.txt" required \
    bash -lc 'cd frontend/dashboards && npm ci'
  run_capture "Frontend lint" "22_FRONTEND_LINT.txt" required \
    bash -lc 'cd frontend/dashboards && npm run lint'
  run_capture "Frontend build" "23_FRONTEND_BUILD.txt" required \
    bash -lc 'cd frontend/dashboards && npm run build'
  run_capture "Frontend tests" "24_FRONTEND_TESTS.txt" review \
    bash -lc 'cd frontend/dashboards && npm test -- --run'
else
  add_gate "Frontend directory exists" "FAIL" "20_FRONTEND_PACKAGE_FILES.txt" "frontend/dashboards directory not found."
  add_gate "Frontend install" "FAIL" "21_FRONTEND_INSTALL.txt" "frontend/dashboards directory not found."
  add_gate "Frontend lint" "FAIL" "22_FRONTEND_LINT.txt" "frontend/dashboards directory not found."
  add_gate "Frontend build" "FAIL" "23_FRONTEND_BUILD.txt" "frontend/dashboards directory not found."
  add_gate "Frontend tests" "FAIL" "24_FRONTEND_TESTS.txt" "frontend/dashboards directory not found."
fi

# ==========================================================
# 5. LIVE RUNTIME PROOF
# ==========================================================
echo ""
echo "Enter live backend base URL."
echo "Example: https://your-backend.azurewebsites.net"
echo "Leave blank to mark runtime proof FAIL."
read -r BACKEND_BASE_URL

echo ""
echo "Enter live frontend URL."
echo "Example: https://your-frontend.azurestaticapps.net"
echo "Leave blank to mark frontend runtime proof FAIL."
read -r FRONTEND_BASE_URL

{
  echo "BackendBaseUrl=$BACKEND_BASE_URL"
  echo "FrontendBaseUrl=$FRONTEND_BASE_URL"
} > "$OUT/30_RUNTIME_URLS.txt"

if [ -n "$BACKEND_BASE_URL" ]; then
  run_capture "Live backend health endpoint" "31_LIVE_BACKEND_HEALTH.json" required \
    bash -lc "curl -fsS '${BACKEND_BASE_URL%/}/api/health/'"
  if [ -n "$INTEGRITY_SCHOOL_ID" ]; then
    run_capture "Live backend integrity endpoint" "32_LIVE_BACKEND_INTEGRITY.json" required \
      bash -lc "curl -fsS -H 'X-School-Id: ${INTEGRITY_SCHOOL_ID}' '${BACKEND_BASE_URL%/}/api/integrity/'"
  else
    add_gate "Live backend integrity endpoint" "REVIEW" "32_LIVE_BACKEND_INTEGRITY.json" "Set INTEGRITY_SCHOOL_ID or CROWN_PACKET_SCHOOL_ID to probe tenant-scoped integrity endpoint."
  fi
else
  add_gate "Live backend health endpoint" "FAIL" "31_LIVE_BACKEND_HEALTH.json" "No backend URL entered."
  add_gate "Live backend integrity endpoint" "FAIL" "32_LIVE_BACKEND_INTEGRITY.json" "No backend URL entered."
fi

if [ -n "$FRONTEND_BASE_URL" ]; then
  run_capture "Live frontend reachability" "33_LIVE_FRONTEND_REACHABILITY.txt" required \
    bash -lc "curl -I -fsS '${FRONTEND_BASE_URL%/}/'"
else
  add_gate "Live frontend reachability" "FAIL" "33_LIVE_FRONTEND_REACHABILITY.txt" "No frontend URL entered."
fi

# ==========================================================
# 6. AZURE PROOF
# ==========================================================
if command -v az >/dev/null 2>&1; then
  run_capture "Azure account proof" "40_AZURE_ACCOUNT.txt" required az account show
  run_capture "Azure resource inventory" "41_AZURE_RESOURCES.json" required az resource list --output json
  run_capture "Azure webapp inventory" "42_AZURE_WEBAPPS.json" review az webapp list --output json
else
  add_gate "Azure CLI installed" "FAIL" "40_AZURE_ACCOUNT.txt" "az CLI not found in Codespace."
  add_gate "Azure resource inventory" "FAIL" "41_AZURE_RESOURCES.json" "az CLI not found in Codespace."
  add_gate "Azure webapp inventory" "FAIL" "42_AZURE_WEBAPPS.json" "az CLI not found in Codespace."
fi

# ==========================================================
# 7. 12x12 / 51x51 / WIZARD / REMEDIATION ARTIFACT TIE-OUT
# ==========================================================
run_capture "Find 12x12 artifacts" "50_FIND_12X12_ARTIFACTS.txt" required \
  bash -lc "find . -type f | grep -Ei '12x12|12-x-12|process' | sort"
run_capture "Find 51x51 artifacts" "51_FIND_51X51_ARTIFACTS.txt" required \
  bash -lc "find . -type f | grep -Ei '51x51|51-x-51|module-integrity|MODULE_INTEGRITY|FIX_MATRIX|fix_matrix' | sort"
run_capture "Find wizard artifacts" "52_FIND_WIZARD_ARTIFACTS.txt" required \
  bash -lc "find . -type f | grep -Ei 'wizard|WIZARD' | sort"
run_capture "Find remediation artifacts" "53_FIND_REMEDIATION_ARTIFACTS.txt" required \
  bash -lc "find audit-artifacts -type f 2>/dev/null | grep -Ei 'remediation|REMEDIATION|fix|FIX|fail|FAIL|review|REVIEW' | sort"
run_capture "Backend module directory inventory" "54_BACKEND_MODULE_DIRECTORY_INVENTORY.txt" required \
  bash -lc "find backend -maxdepth 2 -type d | sort"
run_capture "Backend wizard directory inventory" "55_BACKEND_WIZARD_DIRECTORY_INVENTORY.txt" required \
  bash -lc "find backend -maxdepth 2 -type d | grep -Ei 'wizard' | sort"

# ==========================================================
# 8. DASHBOARD KPI TRUTH MATRIX
# Fill this manually after review.
# ==========================================================
if [ -n "$DASHBOARD_KPI_MATRIX_SOURCE" ] && [ -f "$DASHBOARD_KPI_MATRIX_SOURCE" ]; then
  cp "$DASHBOARD_KPI_MATRIX_SOURCE" "$OUT/60_DASHBOARD_KPI_TRUTH_MATRIX.csv"
else
cat > "$OUT/60_DASHBOARD_KPI_TRUTH_MATRIX.csv" <<'CSV'
Dashboard,KPI,Status,SourceFileOrEndpoint,ProofNotes
Admin Command Center,,REVIEW,,
Admissions,,REVIEW,,
Attendance,,REVIEW,,
Billing/Finance,,REVIEW,,
Communications,,REVIEW,,
Gradebook,,REVIEW,,
Parent Portal,,REVIEW,,
Teacher Portal,,REVIEW,,
Sandbox Operator,,REVIEW,,
CSV
fi

evaluate_matrix_gate \
  "Dashboard KPI truth matrix created" \
  "60_DASHBOARD_KPI_TRUTH_MATRIX.csv" \
  "Fill every KPI as LIVE_MODEL_BACKED, SANDBOX_SEED_BACKED, STATIC_DEMO_BACKED, or NOT_IMPLEMENTED."

# ==========================================================
# 9. SANDBOX SMOKE PROOF MATRIX
# Fill this manually or with Playwright proof.
# ==========================================================
if [ -n "$SANDBOX_SMOKE_MATRIX_SOURCE" ] && [ -f "$SANDBOX_SMOKE_MATRIX_SOURCE" ]; then
  cp "$SANDBOX_SMOKE_MATRIX_SOURCE" "$OUT/70_SANDBOX_SMOKE_PROOF_MATRIX.csv"
else
cat > "$OUT/70_SANDBOX_SMOKE_PROOF_MATRIX.csv" <<'CSV'
SmokePath,RequiredResult,Status,ProofFile,Notes
Admin login,Can log in with sandbox credentials,REVIEW,,
Teacher login,Can log in with sandbox credentials,REVIEW,,
Parent login,Can log in with sandbox credentials,REVIEW,,
Admissions flow,Loads and operates without fatal errors,REVIEW,,
Attendance flow,Loads and operates without fatal errors,REVIEW,,
Gradebook flow,Loads and operates without fatal errors,REVIEW,,
Finance/Billing flow,Loads and operates without fatal errors,REVIEW,,
Communications flow,Loads and operates without fatal errors,REVIEW,,
Tenant isolation,No cross-school data bleed,REVIEW,,
Sandbox/production separation,No production data or credentials shown,REVIEW,,
Console check,No fatal browser console errors,REVIEW,,
Feedback intake,GitHub issue template/path works,REVIEW,,
CSV
fi

evaluate_matrix_gate \
  "Sandbox smoke matrix created" \
  "70_SANDBOX_SMOKE_PROOF_MATRIX.csv" \
  "Fill with PASS only after live browser or Playwright proof."

# ==========================================================
# 10. FINAL COUNTS / DECISION
# ==========================================================
PASS_COUNT="$(awk -F, 'NR>1 && $2 ~ /PASS/ {c++} END {print c+0}' "$GATE_CSV")"
REVIEW_COUNT="$(awk -F, 'NR>1 && $2 ~ /REVIEW/ {c++} END {print c+0}' "$GATE_CSV")"
FAIL_COUNT="$(awk -F, 'NR>1 && $2 ~ /FAIL/ {c++} END {print c+0}' "$GATE_CSV")"
TOTAL_COUNT="$(( $(wc -l < "$GATE_CSV") - 1 ))"

if [ "$FAIL_COUNT" -eq 0 ] && [ "$REVIEW_COUNT" -eq 0 ]; then
  FINAL_DECISION="GO"
  FINAL_TEXT="GO FOR GENERAL PRODUCTION RELEASE"
else
  FINAL_DECISION="NO-GO"
  FINAL_TEXT="NO-GO FOR GENERAL PRODUCTION RELEASE"
fi

cat > "$SUMMARY" <<EOF
# CROWN Final Production Release Proof Packet

Timestamp: $STAMP
Commit SHA: $HEAD_SHA
Branch: $BRANCH

## Gate Counts
- PASS: $PASS_COUNT
- REVIEW: $REVIEW_COUNT
- FAIL: $FAIL_COUNT
- TOTAL: $TOTAL_COUNT

## Binary Decision
$FINAL_DECISION

## Production GO Rule
General production release is GO only when:
- PASS = TOTAL
- FAIL = 0
- REVIEW = 0
- runtime proof is green
- Azure proof is green
- GitHub ruleset/branch protection proof is green
- backend proof is green
- frontend proof is green
- sandbox smoke proof is green
- dashboard KPI truth matrix is complete
- 12x12, 51x51, wizard, and remediation artifacts are tied to this same commit SHA

## Evidence Folder
$OUT

## Next Action
$(if [ "$FINAL_DECISION" = "GO" ]; then echo "Tag the release, create the final release note, and freeze the packet."; else echo "Open GATE_RESULTS.csv, resolve every FAIL and REVIEW row, rerun the packet, and do not declare production GO yet."; fi)
EOF

cat > "$DECISION" <<EOF
# Final Decision

## Decision
$FINAL_TEXT

## Counts
- PASS: $PASS_COUNT
- REVIEW: $REVIEW_COUNT
- FAIL: $FAIL_COUNT
- TOTAL: $TOTAL_COUNT

## Commit
$HEAD_SHA

## Evidence Folder
$OUT

## Required next action
$(if [ "$FINAL_DECISION" = "GO" ]; then echo "Tag the release, create the final release note, and freeze the packet."; else echo "Open GATE_RESULTS.csv, resolve every FAIL and REVIEW row, rerun this packet, and do not declare production GO yet."; fi)
EOF

echo ""
echo "============================================================"
echo "DONE: Final proof packet created"
echo "============================================================"
echo "Evidence folder: $OUT"
echo ""
echo "PASS:   $PASS_COUNT"
echo "REVIEW: $REVIEW_COUNT"
echo "FAIL:   $FAIL_COUNT"
echo "TOTAL:  $TOTAL_COUNT"
echo ""
echo "Decision: $FINAL_DECISION"
echo ""
echo "Open these:"
echo "  $GATE_CSV"
echo "  $SUMMARY"
echo "  $DECISION"
echo ""
