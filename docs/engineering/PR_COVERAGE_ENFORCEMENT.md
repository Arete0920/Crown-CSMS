# Governed pull-request coverage enforcement

Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.
Owner: CROWN product owner; October 9, 2026 instruction to proceed.
Scope: wire existing governed coverage execution into required `pytest-internal` check.
Forbidden scope: threshold changes, exclusion changes, test removal, production activation.
Rollback: revert this outcome PR.

The Tests workflow runs the existing `run_backend_coverage.ps1` runner against the full
backend pytest suite. Coverage tooling is fixed at 7.16.2. The existing evaluator,
reviewed operational-inclusive boundary, and unchanged 75% threshold remain authoritative.
Broad backend coverage remains a separately reported repository-health metric.

Tests, JUnit, coverage JSON/XML, governed evaluation, source identity, and artifact hashes
are retained for 14 days and uploaded even when execution fails. Missing evidence blocks
the check. This replaces the existing full-suite invocation rather than adding a second
full-suite run. The protected check name remains `pytest-internal`.

Hosted coverage percentage, exact-head CI, and merge remain NOT VERIFIED until execution.
No deployment or operational assurance is asserted by a passing source coverage gate.
