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

## DEV browser evidence exports

The DEV preview job uses `scripts/run-dev-browser-evidence.mjs` from
`frontend/dashboards` for its certification, buyer, and tenant-isolation suites.
The certification suite retains the existing preflight-then-crawler sequence;
a failed preflight prevents the crawler from starting. The production commands
and deployment triggers are unchanged.

Each execution uses a fresh private directory. The custom reporter constructs
JSON from an explicit schema: fixed repository and phase names, run and attempt,
full source commits, verified source-file hashes, numeric test locations and
ordinals, bounded result statuses, timings, and counts. Test titles, exception
text, output text, attachments, network content, authentication/session values,
and person/school fields are excluded. The DEV-specific configuration disables
trace, screenshot, video, and HTML-report capture. Existing tests may write their
own local diagnostics, but those directories are outside the upload boundary.

The parent runner validates each report after Playwright exits and writes a
fresh publication directory containing only validated JSON. Reporter exceptions
can be swallowed by Playwright, so a successful child exit alone is insufficient:
missing, malformed, stale, wrong-source, or incomplete successful-execution
reports fail the evidence gate. A valid report of a failed test can be retained;
the original test failure still makes the execution step fail.

The three DEV uploads accept only the runner's `evidence_path` when its
`evidence_valid` output is `true`. There is no fallback to `test-results/`,
`playwright-report/`, or application-generated audit directories. Upload names
include the workflow attempt, retain the existing 30-day expiry, and reject a
missing validated output. Durable preservation still requires a separate copy
and retrieval verification before GitHub retention expires.

Source identity is explicit: `CROWN_EVIDENCE_RUNTIME_SHA` identifies the checked-out
and deployed source; `CROWN_EVIDENCE_TEST_SHA` identifies the selected test source;
`CROWN_EVIDENCE_EXPORTER_SHA` identifies the workflow-pinned exporter. Buyer and
tenant test overlays use the workflow source while certification tests use the
runtime source. The exporter verifies the selected files against these commits.
Numeric case identifiers identify source locations and collection order; they
do not disclose runtime titles or parameter values.

Focused local verification:

```bash
cd frontend/dashboards
node --test scripts/dev-browser-evidence.test.mjs
cd ../..
python3 -m unittest discover -s scripts/ops -p test_dev_frontend_deploy_only.py -v
```

These exports are bounded execution records, not complete traces or an automatic
release/certification decision. Historical evidence remains unchanged. Hosted
execution of the new exporter must be verified from its own future run.
