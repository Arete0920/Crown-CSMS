# C1 Deterministic Certification Runbook (Cycles 1-3)

Type: Binary operational certification procedure.

Output states:
- TRUSTED
- FAILED

No intermediate state is valid.

## Preconditions

- Canonical candidate set is loaded in `c1_candidate_sources/`.
- Candidate file count is between 5 and 15.
- No input mutation during certification execution.

## Command

Run from `solomon_governance_c1/`:

```powershell
python .\certify_c1_deterministic_cycles.py
```

## Cycle 1: Baseline Deterministic Capture

Required executions:
- `build_c1_intake_preprocessor.py`
- `verify_c1_control_plane.py`
- `simulate_c1_ingestion_manifest.py`

Required capture:
- SHA256 for each deterministic artifact
- artifact byte size for each deterministic artifact
- row count for each deterministic artifact
- artifact ordering preserved (file-level and row-level, implied by byte identity)

Output artifact:
- `governance/c1/certification/CYCLE1_BASELINE_STATE.json`

## Cycle 2: Repeatability Verification

Required executions:
- Same three scripts as Cycle 1
- Zero input changes

Required comparison against Cycle 1:
- byte identity (SHA256)
- size identity
- row-count identity

Hard fail conditions:
- byte drift
- ordering drift
- lineage drift
- queue mutation
- nondeterministic serialization
- unexplained hash change

Output artifact:
- `governance/c1/certification/CYCLE2_REPLAY_STATE.json`

## Cycle 3: Rebuild Verification

Required actions:
- remove generated artifacts
- regenerate from canonical source files only
- rerun validator and simulator
- compare against Cycle 1 baseline

Required comparison against Cycle 1:
- byte identity (SHA256)
- size identity
- row-count identity

Output artifact:
- `governance/c1/certification/CYCLE3_REBUILD_STATE.json`

## Final Certification Criteria

All must be PASS:
- Cycle 1 complete
- Cycle 2 deterministic replay
- Cycle 3 deterministic rebuild
- Validator fail-closed
- Provenance lineage stable
- Quarantine propagation stable
- No hidden state detected
- No uncontrolled mutation detected

Result artifact:
- `governance/c1/certification/CERTIFICATION_RESULT.json`

Final console output:
- `TRUSTED` if all criteria pass
- `FAILED` if any criterion fails

## Deterministic Artifact Set Under Certification

- `registers/source_candidates.csv`
- `registers/evidence_register.csv`
- `registers/review_queue.csv`
- `registers/human_approval_queue.csv`
- `registers/risk_exceptions.csv`
- `simulation/ingestion_simulation_manifest.csv`
- `simulation/chunk_boundary_manifest.csv`
- `simulation/provenance_inheritance_manifest.csv`
- `simulation/quarantine_propagation_manifest.csv`

## Safety Rule

A single unexplained drift event fails the cycle.

No warning-only behavior is allowed.
