# Crown Business Observability Standard

Technical health is not business health. Crown must record enough structured evidence to answer whether the underlying school operation succeeded.

## Minimum structured context

- correlation/request identifier;
- tenant/school identifier where applicable;
- authenticated actor identifier where safe;
- business operation;
- authoritative entity identifier;
- result classification;
- elapsed time;
- safe error classification.

## Priority outcome measures

Application conversion, enrollment conversion, failed/retried payments, reconciliation exceptions, dead outbox messages, tenant-denial events, failed imports, aid posting failures, stale integrations, and critical background-job retries.

A green HTTP response, worker completion, or page render is not sufficient evidence of business success when persistence or downstream delivery is part of the operation.
