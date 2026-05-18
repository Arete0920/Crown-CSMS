# C1 Fail-Closed Activation Gates

Type: Binary activation control.

Activation decision outputs:
- ALLOW
- DENY

No warning-only path is valid.

## Gate Command

Run from `solomon_governance_c1/`:

```powershell
python .\enforce_c1_activation_gate.py ingestion
```

Substitute `ingestion` with any requested capability:
- `ingestion`
- `chunking`
- `embeddings`
- `retrieval`
- `orchestration`
- `automation`

## Required Checks (All MUST PASS)

1. validator_pass
2. simulation_pass
3. reproducibility_confirmation
4. golden_corpus_stable
5. human_approval_record
6. clean_quarantine_state
7. deterministic_certification

## Failure Behavior

If any check fails:
- decision = `DENY`
- activation remains blocked
- gate report is emitted for audit

## Gate Report Location

`governance/c1/gates/<capability>_activation_gate.json`

## Safety Doctrine

- No irreversible state transitions without prior deterministic simulation.
- Every capability expansion must be denied by default until explicitly proven safe.
