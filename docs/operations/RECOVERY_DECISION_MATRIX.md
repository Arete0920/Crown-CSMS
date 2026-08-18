# Recovery Decision Matrix

**Current authority:** `docs/CURRENT_RELEASE_STATUS.md` plus the authorized owner-handoff/operational-transfer record for the selected exact identity.  
**Scope:** repository-level decision simulation only; no Azure or production mutation.  
**Historical note:** predecessor recovery issue numbers are provenance only and are not current Crown-CSMS execution authority.

This control verifies four required branches:

1. healthy runtime after deployment automation failure: preserve the runtime and investigate automation;
2. unhealthy runtime with immutable image available: select exact last-known-good image rollback;
3. unavailable runtime without image but with restore evidence: enter manual control with restore fallback;
4. no verified rollback or restore control: fail closed and escalate.

The workflow checks out the exact PR head SHA, records that SHA in every packet, and records decision-control elapsed time in milliseconds. This is not application rollback RTO or database restore RTO. Actual application rollback, isolated restore validation, tenant/application validation, exact runtime identity, and authorized acceptance remain separately required where applicable to final operational handoff or a selected production release.

Planning targets remain:

- application rollback RTO: 30 minutes;
- isolated database restore validation RTO: 4 hours;
- database RPO: 1 hour.

Repository decision simulation does not imply production deployment, production authorization, operational recovery completion, or completed owner turnover.
