#!/usr/bin/env bash
set -euo pipefail

ROOT="/workspaces/Crown2026"
if [ ! -d "$ROOT" ]; then
  ROOT="$(pwd)"
fi
cd "$ROOT"

CUR="audit-artifacts/sandbox-launch-5schools/current"
mkdir -p "$CUR" scripts

# -----------------------------------------------------------------------------
# Seed the six live files if missing
# -----------------------------------------------------------------------------
[ -f "$CUR/01_school_matrix.csv" ] || cat > "$CUR/01_school_matrix.csv" <<'EOF'
school_code,school_name,tenant_slug,base_url,login_url,admin_account,parent_account,teacher_account,finance_account,admissions_account,login_status,landing_status,notes,owner
S01,Heritage Christian Academy,heritage,,/login/,,,,,,,not done,not done,,Operator A
S02,Harvest Christian School,harvest,,/login/,,,,,,,not done,not done,,Operator A
S03,Faith Academy,faith,,/login/,,,,,,,not done,not done,,Operator A
S04,Calvary Christian School,calvary,,/login/,,,,,,,not done,not done,,Operator B
S05,St. Anne's Academy,st-annes,,/login/,,,,,,,not done,not done,,Operator B
EOF

[ -f "$CUR/02_role_flow_matrix.csv" ] || cat > "$CUR/02_role_flow_matrix.csv" <<'EOF'
school_code,role,user_identifier,login_pass,landing_pass,primary_flow,primary_flow_status,tenant_boundary_status,notes,owner
S01,School Administrator,,not done,not done,admin dashboard + action path,not done,not done,,Dev 5
S01,Parent,,not done,not done,parent portal core path,not done,not done,,Dev 5
S01,Teacher,,not done,not done,teacher portal core path,not done,not done,,Dev 5
S01,Finance,,not done,not done,finance dashboard + invoice/billing path,not done,not done,,Dev 3
S01,Admissions,,not done,not done,admissions dashboard + intake path,not done,not done,,Dev 3
S02,School Administrator,,not done,not done,admin dashboard + action path,not done,not done,,Dev 5
S02,Parent,,not done,not done,parent portal core path,not done,not done,,Dev 5
S02,Teacher,,not done,not done,teacher portal core path,not done,not done,,Dev 5
S02,Finance,,not done,not done,finance dashboard + invoice/billing path,not done,not done,,Dev 3
S02,Admissions,,not done,not done,admissions dashboard + intake path,not done,not done,,Dev 3
S03,School Administrator,,not done,not done,admin dashboard + action path,not done,not done,,Dev 5
S03,Parent,,not done,not done,parent portal core path,not done,not done,,Dev 5
S03,Teacher,,not done,not done,teacher portal core path,not done,not done,,Dev 5
S03,Finance,,not done,not done,finance dashboard + invoice/billing path,not done,not done,,Dev 3
S03,Admissions,,not done,not done,admissions dashboard + intake path,not done,not done,,Dev 3
S04,School Administrator,,not done,not done,admin dashboard + action path,not done,not done,,Dev 5
S04,Parent,,not done,not done,parent portal core path,not done,not done,,Dev 5
S04,Teacher,,not done,not done,teacher portal core path,not done,not done,,Dev 5
S04,Finance,,not done,not done,finance dashboard + invoice/billing path,not done,not done,,Dev 3
S04,Admissions,,not done,not done,admissions dashboard + intake path,not done,not done,,Dev 3
S05,School Administrator,,not done,not done,admin dashboard + action path,not done,not done,,Dev 5
S05,Parent,,not done,not done,parent portal core path,not done,not done,,Dev 5
S05,Teacher,,not done,not done,teacher portal core path,not done,not done,,Dev 5
S05,Finance,,not done,not done,finance dashboard + invoice/billing path,not done,not done,,Dev 3
S05,Admissions,,not done,not done,admissions dashboard + intake path,not done,not done,,Dev 3
EOF

[ -f "$CUR/03_blocker_log.csv" ] || cat > "$CUR/03_blocker_log.csv" <<'EOF'
id,opened_at,area,severity,blocker,status,owner,fix_commit_or_note,retest_status
EOF

[ -f "$CUR/04_risk_register.csv" ] || cat > "$CUR/04_risk_register.csv" <<'EOF'
id,opened_at,risk,severity,probability,mitigation,owner,next_review,status
EOF

[ -f "$CUR/05_hourly_scoreboard.csv" ] || cat > "$CUR/05_hourly_scoreboard.csv" <<'EOF'
checkpoint,runtime_health,runtime_integrity,school_matrix,role_flows,tenant_proof,frontend_lint,frontend_build,notes,status
H+00,completed and verified,completed and verified,in progress,in progress,in progress,completed and verified,completed and verified,baseline loaded,in progress
H+03,in progress,in progress,in progress,in progress,in progress,in progress,in progress,,in progress
H+06,in progress,in progress,in progress,in progress,in progress,in progress,in progress,,in progress
H+09,in progress,in progress,in progress,in progress,in progress,in progress,in progress,,in progress
H+12,in progress,in progress,in progress,in progress,in progress,in progress,in progress,,in progress
EOF

[ -f "$CUR/20_final_go_no_go.md" ] || cat > "$CUR/20_final_go_no_go.md" <<'EOF'
# Final Go / No-Go

Runtime health:
- completed and verified

Runtime integrity:
- completed and verified

5-school login matrix:
- in progress

Role-flow proof:
- in progress

Tenant proof:
- in progress

Blocker count:
- in progress

Residual risks:
- in progress

Tomorrow-morning recommendation:
- in progress
EOF

# ...rest of script omitted for brevity...
