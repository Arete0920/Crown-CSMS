#!/usr/bin/env bash
set -euo pipefail

# Deterministic local CI-proof harness for workflow authoring gates.
# Runs the same proof command N times and records per-run evidence.

RUNS="${1:-5}"
OUTDIR="${2:-audit-artifacts/solomon-start/s001-ci-baseline}"
PROOF_CMD=(pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/validate-workflows.ps1)

if ! [[ "$RUNS" =~ ^[0-9]+$ ]] || [[ "$RUNS" -lt 1 ]]; then
  echo "ERROR: RUNS must be a positive integer. Got: $RUNS" >&2
  exit 2
fi

if ! command -v pwsh >/dev/null 2>&1; then
  echo "ERROR: pwsh is required but not found on PATH." >&2
  exit 3
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

mkdir -p "$OUTDIR"

SUMMARY_FILE="$OUTDIR/03_ci_stress_summary.tsv"
META_FILE="$OUTDIR/04_ci_stress_meta.txt"

echo -e "run\texit_code\tstarted_utc\tfinished_utc\tlog_file" > "$SUMMARY_FILE"

echo "Harness: scripts/ci-stress-test.sh" > "$META_FILE"
echo "Proof command: ${PROOF_CMD[*]}" >> "$META_FILE"
echo "Runs: $RUNS" >> "$META_FILE"
echo "Started UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$META_FILE"

pass_count=0

for ((i=1; i<=RUNS; i++)); do
  started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  log_file="$OUTDIR/run_${i}.log"

  echo "[S-001] run $i/$RUNS started at $started" | tee "$log_file"

  set +e
  "${PROOF_CMD[@]}" >> "$log_file" 2>&1
  code=$?
  set -e

  finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  if [[ "$code" -eq 0 ]]; then
    pass_count=$((pass_count + 1))
    echo "[S-001] run $i PASS" >> "$log_file"
  else
    echo "[S-001] run $i FAIL (exit $code)" >> "$log_file"
  fi

  echo -e "$i\t$code\t$started\t$finished\t$log_file" >> "$SUMMARY_FILE"
done

echo "Finished UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$META_FILE"
echo "Pass count: $pass_count/$RUNS" >> "$META_FILE"

if [[ "$pass_count" -ne "$RUNS" ]]; then
  echo "S-001 RESULT: FAIL ($pass_count/$RUNS passes). See $SUMMARY_FILE" >&2
  exit 1
fi

echo "S-001 RESULT: PASS ($pass_count/$RUNS passes). Evidence in $OUTDIR"
