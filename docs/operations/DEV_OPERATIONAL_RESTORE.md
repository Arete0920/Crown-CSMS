# DEV backup into disposable CI PostgreSQL

Scope: issue #427. This is a manually authorized recovery exercise, not a
deployment, schema stage, credential change, release or refresh activation.

The existing **Isolated PostgreSQL Restore Drill** workflow retains its generated
fixture mode. Its separate operational mode requires current protected main,
`dev_operational_restore=true`, its exact full `expected_dev_sha`,
`confirm_dev_restore=restore-dev-backup-in-ci`, and
`synthetic_dev_confirmed=true`. The last input records an actual owner data-origin
attestation; environment markers alone cannot prove that data is synthetic.
Do not select it without that attestation and explicit recovery authority.

The operational source is fixed to the existing DEV App Service and PostgreSQL
host, verified environment markers, database-identity digest and verified TLS.
There is no production fallback. A repeatable read-only source transaction
exports a snapshot used by both row-count checks and `pg_dump`. The backup's
creation interval, size and digest are retained without database contents.
Source PostgreSQL versions 13–16 are supported by the isolated PostgreSQL 16
client/restore service; other versions fail closed and require review.

Every write occurs through the job service's container ID, the local Docker
socket and explicit loopback PostgreSQL settings. Ambient libpq service, host,
password, Django and Azure settings are not inherited into the restore process.
An existing restore database is rejected, not deleted. Generated database names
are bound to the run/attempt. Creation uncertainty and restore failure still
attempt cleanup of that unique disposable target. Cleanup failure blocks PASS.

The runner verifies every public table's exact row count, column definitions
and migration history against the exported source snapshot. PostgreSQL restore
errors, including constraint failures, block acceptance. Offline negative tests
and a real generated-fixture dump/restore plus corrupt-archive test run before
the operational job can authenticate to Azure.

Only `dev-restore-evidence.json` is uploaded for seven days. Dump bytes,
credentials, row contents and raw process diagnostics must never be artifacts
or issue comments. Private temporary backup files are removed on success and
failure; the service container is destroyed by the job. This test does not
create a durable operational backup archive or change Azure retention policy.

The runner records a fixed `recovery_stage` and maps recognized client failures
to fixed categories without copying stderr, names, URLs or statement text.
These categories are diagnostic hints, not independent root-cause proof; unknown
or localized failures retain `postgres_process_failed`. The disposable client's
CA bundle must be present before DEV credentials are retrieved. Missing or
unreadable trust material fails closed; never disable certificate verification
to complete the exercise. Correct client prerequisites through protected source
review and rerun only under the existing bounded authority at accepted main.

A passing result establishes this snapshot's dump/restore and recorded integrity
checks. It does not establish application rollback-image compatibility, total
recovery RTO, accepted RPO, deployed source parity, provisioning or release
readiness. Those remain separately evidenced gates. Reconcile all evidence with
the actual accepted source and do not use a fixture result as DEV recovery proof.

Rollback of runner source: revert its bounded PR through protected checks.
Operational cleanup affects only the unique CI database and ephemeral archive;
there is no source DEV database mutation to reverse.
