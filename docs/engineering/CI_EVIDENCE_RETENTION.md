# CI evidence retention and execution efficiency

Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.
Owner authorization: October 9, 2026 instruction to implement repository CI hardening.
Scope: bounded artifact storage, explicit missing-file behavior, obsolete PR cancellation,
and read-only weekly CI metrics. Rollback: revert this outcome PR.

All artifact uploads have explicit 1–30 day retention and missing-file behavior. Newly
specified diagnostic/source artifacts use 14 days; existing explicit retention is preserved.
Mandatory production certification upload rejects missing evidence. Optional browser/stale
branch diagnostics retain their explicit warn/ignore behavior. Required Repository Policy
rejects absent retention, absent missing-file policy, and whole-worktree/history uploads.
Release Verify now uploads its generated schema rather than copying historical release docs.

Dependency audit, dependency admission and secret scan cancel superseded PR runs. Main,
production, schema and recovery cancellation behavior is unchanged.

The existing permissions audit runs weekly and retains bounded read-only Actions metrics:
queue time, job duration, retries, failed job names, source heads and artifact bytes. The
sample covers 20 completed PR workflow runs; it is not a complete 20-PR baseline or billing
report. Incomplete timing is explicitly marked. Metrics cannot authorize merge or release.

Local artifact-policy rejection tests, metrics accounting tests and checksum-verified
workflow lint must pass. Hosted CI, actual storage savings, and merge remain NOT VERIFIED.
Durable operational evidence retention remains a separate approved operational control.
