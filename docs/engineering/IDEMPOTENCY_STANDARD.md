# Crown Idempotency Standard

Every consequential mutation must be safe to retry when network, worker, user, or provider behavior can repeat the request.

## Required cases

- payment creation, webhook processing, refund, settlement and reconciliation;
- financial-aid ledger posting;
- enrollment conversion and contract/deposit transitions;
- email/SMS outbox delivery;
- imports and batch operations;
- CrownPass issuance/redemption;
- provisioning and external connector writes.

## Contract

Use a stable business idempotency key or an authoritative uniqueness constraint. A retry must return or recognize the original result rather than duplicate the business effect. Retryable transport failure and permanent business rejection must remain distinguishable.
