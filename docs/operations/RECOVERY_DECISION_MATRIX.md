# Recovery Decision Matrix

**Controlling issue:** #1270  
**Scope:** repository-level decision simulation only; no Azure or production mutation.

This control verifies four required branches:

1. healthy runtime after deployment automation failure: preserve the runtime and investigate automation;
2. unhealthy runtime with immutable image available: select exact last-known-good image rollback;
3. unavailable runtime without image but with restore evidence: enter manual control with restore fallback;
4. no verified rollback or restore control: fail closed and escalate.

The workflow checks out the exact PR head SHA, records that SHA in every packet, and records decision-control elapsed time in milliseconds. This is not application rollback RTO or database restore RTO. Actual Azure rollback, isolated restore validation, tenant/application validation, and Product Owner acceptance remain required for #1270 closure.

Planning targets remain:

- application rollback RTO: 30 minutes;
- isolated database restore validation RTO: 4 hours;
- database RPO: 1 hour.

Production authorization is not implied.
