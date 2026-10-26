# DEV schoolless operations credential verification

This helper implements only the bounded reset-credential check in issue #269.
It does not rotate credentials or certify secret-store retirement, consumers,
diagnostic authorization, other environments, or issue closure.

Use an approved operator facility after coordinating exclusive Azure mutation
ownership and recording the actual App Service/slot, effective settings/Key Vault
routing, runtime variable precedence, store changes, authorized Actions/operator/
sandbox consumers and rollback. Preserve unrelated settings. Do not execute reset
workflows, provisioning, recovery or migrations for this check.

The facility must securely inject `CROWN_RETIRED_OPS_SECRET` and
`CROWN_REPLACEMENT_OPS_SECRET` into the verifier process. Obtain the historical
credential only from its approved secured holding; never retrieve it from public
history. Generate/store the replacement through the approved secret-management
mechanism. Never put either credential in command arguments, shell history,
transcripts, source, evidence or public workflow logs. No secret hashes are emitted.
Remove the temporary process bindings when verification is finished.

Run from the reviewed checkout with Python 3.12:

```text
python scripts/ops/verify_dev_ops_credential_retirement.py --expected-runtime-sha <reviewed-deployed-full-sha>
```

The SHA is the independently identified and source-reviewed deployed DEV runtime;
do not substitute current main unless actually deployed. This distinction permits
credential retirement while separate deployment parity remains open in #427.

The target is fixed to `https://crown-api-dev.azurewebsites.net`. The helper
requires healthy DEV health/build/artifact identity before credentials are sent,
rejects redirects and first requires replacement POST400 with the exact
missing-school validation. It then requires historical POST403 with the exact
credential-denial response, followed by the same healthy runtime identity. A
disabled DEV gate, generic 403, redirect or runtime movement cannot pass. Both
POSTs use an empty JSON object and no school header or query. The helper accepts
no host, school selector, request-body option or credential argument. Raw response
bodies, credential values and exception details are withheld.

Exit 0 means **only the reset-credential probe passed**; exit 2 is BLOCKED. Retain
the sanitized JSON with operator identity, UTC store/consumer receipts and
independent service health evidence. Keep #269 open until every acceptance item
is evidenced. Never interpret a probe PASS as certification of all consumers.
A single request sequence does not establish credential convergence across every
App Service worker or instance; retain the separate rollout/reload evidence.

Diagnostic authorization is deliberately not called by this helper: it never
sends the replacement credential to a DB-reading endpoint. The issue's separate
approved historical-only `X-Ops-Secret` denial check remains an operator task;
withhold diagnostic response bodies and never execute an authorized diagnostic.
