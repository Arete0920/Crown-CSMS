# Protected-Spine Admissions Isolation: Nav Endpoint Process-Hang Repro (2026-05-29)

Purpose: capture deterministic evidence for the admissions-applications first blocker recorded in protected-spine subbatch stamp `20260529_045703`.

## Context

- Runtime packet exists: `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_045703.md`.
- First blocker in packet: `admissions-applications`.
- Blocker type: `proof_runner_failure` with `runner_error=nonzero_exit_without_product_failure_signal`.

## Commands Run

- File-level probe:
  - `.venv/Scripts/python.exe -u -m pytest backend/core/tests/test_nav_endpoint.py -q -x --nomigrations`
- Node-level bisection:
  - `.venv/Scripts/python.exe -u -m pytest backend/core/tests/test_nav_endpoint.py::TestNavTenantEnforcement::test_missing_school_id_header_returns_400 -q -x --nomigrations`
  - `.venv/Scripts/python.exe -u -m pytest backend/core/tests/test_nav_endpoint.py::TestNavResponseShape::test_school_scoping_cross_tenant_isolation -q -x --nomigrations`

All probes were run under a hard process timeout wrapper.

## Results

- File-level probe:
  - stdout footer observed: `11 passed in 10.29s`.
  - process outcome: `TIMEOUT` (process did not terminate before timeout).
- Node-level probe #1:
  - stdout footer observed: `1 passed in 2.29s`.
  - process outcome: `TIMEOUT`.
- Node-level probe #2:
  - stdout footer observed: `1 passed in 3.89s`.
  - process outcome: `TIMEOUT`.

## Interpretation

- Product tests in `backend/core/tests/test_nav_endpoint.py` are passing.
- The blocker is process lifecycle/teardown behavior after successful pytest execution, not a direct product assertion failure.
- This behavior is consistent with the wrapper packet classification: `proof_runner_error` + `nonzero_exit_without_product_failure_signal`.

## Release Impact

- P0-3 remains OPEN.
- Runtime packet publication is complete for stamp `20260529_045703`, but packet is RED until the admissions proof-runner failure class is resolved and packet is republished green with policy-gate linkage on candidate SHA.
