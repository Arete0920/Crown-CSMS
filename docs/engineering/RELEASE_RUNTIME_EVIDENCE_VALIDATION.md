# Release runtime evidence validation

Base: `d3e454e785b6d9ecd54dc114acc4370d18e934a9`.
Scope: five runtime certification consumers, their common validator/helper, regression tests, and this record. Rollback: revert this bounded repair; never replace a failing runtime result with success.

The prior domain-model, data-migration, financial-controls, performance, and observability scripts unconditionally emitted failure and could not ingest executed proof. They now validate proof before promoting a control. Their existing control inventories and static prerequisites remain intact. Missing proof remains failure. This repair supplies an ingestion path; it does not supply operational evidence or certify a deployment.

Set `CROWN_RELEASE_RUNTIME_EVIDENCE` to a sanitized JSON evidence packet and `CROWN_RELEASE_EVIDENCE_ENVIRONMENT` to the intended `sandbox`, `staging`, or `production` environment. Do not commit operational packets or put credentials or student/family information in them.

The packet must contain `schema_version: "1.0"`, complete `source_sha`, `backend_sha`, and `frontend_sha` matching the evaluated Git head, the selected `environment`, opaque `runtime_id`, `run_reference`, and `operator_reference`, and timezone-aware `started_at` and `completed_at` timestamps. Execution must be complete and started within the last 24 hours. These references identify retained runtime and operator evidence; they are not an invented approval or a substitute for review of the underlying run.

Each entry under `gates` uses its consumer name (`domain-model`, `data-migration`, `financial-controls`, `performance`, or `observability`) and contains:

- `junit_path`: a report inside the packet directory;
- `junit_sha256`: the SHA-256 digest of that report;
- `records`: exactly one record for each existing consumer key;
- each record's `key` and `proofs`: a mapping from each required criterion to the executed JUnit `[classname, name]` identity.

Reports must contain no failed, errored, disabled, or skipped proofs, no duplicate case identities, and no empty suite. One executed case cannot be reused to satisfy multiple required proofs. Root-level JUnit `properties` must repeat the packet's source, backend, frontend, environment, runtime, and run identities. Missing, stale, malformed, mismatched, incomplete, or tampered reports fail closed. A `pass: true` assertion or a source keyword count cannot replace executed proof.

| Consumer | Required coverage | Proof criteria for each key |
|---|---|---|
| Domain model | Existing 36 entity keys | model, migration, tenant_boundary, object_authorization, api_surface, workflow_usage, lifecycle, audit, import_export, retention, runtime, current_tests |
| Data migration | Existing 15 domain keys | rehearsal, count_reconciliation, error_reconciliation, rollback, tenant_isolation |
| Financial controls | Existing 15 control keys | runtime_control, ledger_reconciliation |
| Performance | Existing 10 scenario keys | load_test |
| Observability | Existing 10 monitoring and 10 incident keys | executed_control |

Performance records additionally require `measured` and `accepted_targets` objects with numeric `users`, `p95_ms`, and `error_rate`, plus an existing `target_approval_reference`. Measured users must meet the accepted concurrency target; latency and error rate must meet the accepted limits. The executed load testcase must repeat the measured values in its `properties`. No concurrency, latency, or error-rate target is invented by the validator.

Use the existing control definitions when writing runtime tests and reviewing reports. A green JUnit case must actually exercise the named runtime control. Checking a manifest, a fixture, a route string, or a static source token is not operational execution. Synthetic validator fixtures exist only in tests and must never become release evidence.

Validation is supporting evidence. Operational activation, payment processing, legal acceptance, pilot/GA decisions, and final release authorization remain separate and fail closed. No independent human review or operator acceptance is claimed by this change.

Validation: 26 standard-library regression tests exercise passing synthetic proof and rejection of absent/stale/future/mismatched proof, failed/skipped cases, missing control criteria, duplicate cases and properties, non-passing aggregate summaries, reused proof, path traversal, tampering, malformed JSON, and unsupported performance measurements. The Windows contract checks PowerShell parsing and missing-evidence rejection. The approved solo-maintainer control path still requires current exact-head GitHub gates before merge.
