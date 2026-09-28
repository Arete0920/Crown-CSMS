# CROWN Final Production-Readiness Stage

**Authority:** Founder/Product Owner directive  
**Date:** 2026-07-19  
**Controlling issue:** #1374  
**Release target:** Full production release authorization  
**Current decision:** PRODUCTION NOT APPROVED

## 1. Scope boundary

CROWN is in the final production-readiness stage. A controlled sandbox release is not the target and is not an acceptable substitute.

Everything authorized in CROWN is in scope except:

1. **External payment processing:** no processor is selected. All checkout, webhook, fulfillment and manual external-payment confirmation entry points must remain disabled and fail closed. Provider-neutral accounting, billing, ledger, invoice, balance, payment-record and payment-plan functions remain in scope.
2. **Buyer or successor handoff execution:** clean-room transfer, transaction support and ownership-transfer execution are deferred until separately authorized.

No new feature scope enters this stage.

## 2. Single evidence identity

All final evidence must reconcile to one approved and unchanged release identity:

- final repository SHA;
- frontend build identity;
- backend version and health identity;
- deployed image and configuration identity;
- crawler and Playwright evidence;
- operational-drill evidence;
- compliance and final-authority records.

Evidence from different SHAs must not be combined. Any merged code or configuration change after deployment invalidates the prior runtime campaign and returns execution to Stage A.

## 3. Final-stage control loop

### Stage A — settle and freeze the release candidate

Complete before any final runtime proof:

- settle the current scoped PR queue in dependency order;
- merge the external-payment fail-closed change only after exact-head checks pass;
- settle the production-target, recovery/CI, vendor-neutral engineering, ownership and repository-hygiene documentation changes;
- resolve the shared frontend install/test failures affecting `Release Verify` and dependency audit;
- verify all required checks are terminal and green on final `main`;
- generate the complete inventory of active routes, dashboards, modules, wizards, APIs, background tasks, integrations and intentionally disabled surfaces;
- map every inventory item to `CRAWLER`, `PLAYWRIGHT`, `API_CONTRACT`, `BACKEND_TEST`, `OPERATIONAL_DRILL`, `MANUAL_REVIEW`, `EXCLUDED_PAYMENT_PROCESSING`, `EXCLUDED_HANDOFF` or `NOT_APPLICABLE` with rationale;
- freeze the candidate SHA and prohibit unrelated merges until the final decision.

**Stage A exit:** one clean candidate SHA, no unmapped active surface, payment entry points fail closed, and all required repository checks green.

### Stage B — deploy and prove the complete application surface

Deploy the frozen candidate and prove exact frontend, backend and infrastructure identity.

Run the production-mode crawler and Playwright campaign across:

- school administrator;
- teacher;
- parent;
- student;
- board;
- every active dashboard and role redirect;
- every module entry route;
- every wizard and required critical step;
- critical read and write flows for each production-authorized domain;
- authentication, logout, refresh and expired-session handling;
- tenant-header propagation, cross-school denial and privileged override behavior;
- navigation, redirects, network requests, API provenance, console output, screenshots, accessibility and responsive layouts;
- provider-neutral billing and accounting behavior;
- deterministic denial of all excluded external-payment flows.

Tests must fail on identity mismatch, unauthorized access, incorrect tenant context, missing provenance, unexplained required-request failure, unexplained console error, placeholder or fabricated production data, accessibility blocker or active surface omission.

For each failure record route, persona, tenant, request, response, screenshot, root cause and owning issue. Repair only evidence-backed defects. Any repair creates a new candidate identity and restarts at Stage A.

**Stage B exit:** complete mapped surface inventory and full authenticated runtime campaign pass on one unchanged deployed identity.

### Stage C — prove architecture and operational resilience

Complete the remaining production controls:

- tenant middleware, exemptions, structured audit evidence, background-task binding and cleanup under #1352;
- canonical household, guardian and student consumer reconciliation, rehearsal and rollback criteria under #1353;
- controlled application rollback using an immutable prior-known-good image under #1270;
- isolated database restore with representative record and tenant reconciliation under #1270;
- measured and accepted application and database RTO/RPO;
- external secret-store workload and deployment identities under #1294;
- least-privilege retrieval, sanitized audit logging, normal rotation, failed-rotation recovery, revocation and break-glass exercises under #1296;
- incident-response exercise and post-event review.

**Stage C exit:** tenant, canonical-data, recovery and external-secret gates all have accepted binary PASS evidence.

### Stage D — complete compliance and proof governance

Complete:

- student-data inventory and sensitivity classification;
- data-flow and production subprocessor register;
- retention, deletion or anonymization, export and correction procedures;
- privileged support-access verification;
- FERPA, COPPA, PPRA and CIPA applicability and claim boundaries;
- intended-market state student-data privacy review;
- privacy notices, DPA and customer responsibility terms;
- legal review for the approved production scope;
- complete CI workflow, trigger, command, artifact, timeout and proof-owner inventory;
- classification of every workflow as merge gate, release gate, runtime evidence, scheduled assurance, advisory diagnostic or obsolete duplicate;
- consolidation only where equivalence and rollback are proven;
- repository maintainability-pattern remediation for release-relevant active automation and buyer-facing source hygiene, without delaying runtime proof for low-severity cosmetic findings.

**Stage D exit:** compliance/legal scope accepted, CI authority unambiguous, and no unresolved critical or high-severity hygiene defect remains.

### Stage E — reconcile and authorize

After Stages A-D pass on the same release identity:

- update release notes, changelog, deployment, rollback, restore, secrets, compliance and current-status documents;
- link the final evidence packets to #1270, #1274, #1275, #1276, #1277, #1287, #1294, #1296, #1351, #1352, #1353, #1374, #1394, #1425 and #1430 as applicable;
- verify every required check is terminal and green;
- verify no unresolved actionable review thread remains;
- run one final same-SHA production-readiness ceremony;
- record the Founder/Product Owner decision.

**Stage E exit:** explicit production authorization or a documented NO-GO with the exact remaining failed gate.

## 4. Immediate ordered queue

1. Settle PR #1431: fail-close external-payment entry points.
2. Settle PR #1435: production target and final-stage authority.
3. Settle PR #1428: CI ownership and recovery execution packets.
4. Settle PR #1429: vendor-neutral engineering authority.
5. Settle PR #1433: human ownership and engineering-accountability controls.
6. Settle PR #1434: deterministic repository-pattern inventory and stale triage removal.
7. Diagnose and repair the shared frontend `npm ci` / frontend-smoke baseline affecting unrelated PRs.
8. Produce the complete application-surface-to-proof coverage inventory.
9. Add only verified missing crawler, Playwright, API or backend-test coverage.
10. Freeze and deploy the final candidate, then execute Stages B-E without mixing identities.

The PR numbers above are ordered by release dependency, not by creation time. If a PR becomes obsolete or conflicts with the final candidate, close or recut it rather than stacking contradictory authority.

## 5. Production authorization threshold

Production authorization is permitted only when:

- all five stages have passed;
- every active surface is covered or explicitly classified;
- external payment processing is disabled and fail closed;
- handoff execution is outside scope;
- no unresolved critical or high-severity defect remains;
- exact deployed identity, runtime, tenant, recovery, secrets, compliance and CI evidence reconcile to one release SHA;
- release documentation matches actual deployed behavior;
- the Founder/Product Owner records explicit production authorization.

Until then, the target remains full production release and the current decision remains `PRODUCTION NOT APPROVED`.
