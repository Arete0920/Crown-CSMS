# CROWN Azure DEV continuous delivery — controlled rollout policy

**Status: APPROVED ENGINEERING DIRECTION; AUTOMATIC DEPLOYMENT NOT ENABLED.**
Owner: Arete Advisory Group, sole CROWN developer. Tracking: [#687](https://github.com/Arete0920/Crown-CSMS/issues/687). Hosted buyer DEV certification is separately owned by [#427](https://github.com/Arete0920/Crown-CSMS/issues/427); existing invited browser evidence is [PR #685](https://github.com/Arete0920/Crown-CSMS/pull/685).

## Desired service level

After a protected-main merge, automatically assess whether the accepted source can safely advance to the **existing** Azure DEV API and DEV-certification Static Web Apps environment. Target: eligible code-only changes reach exact-SHA DEV parity within **24 hours**. Any blocked release must have a specific error class, evidence, release source SHA and next corrective action; don't suppress freshness failures.

**An accepted PR is not a deployed release.** Separate: source CI → eligible runtime → exact backend/frontend parity → authenticated buyer certification. Never claim one from the evidence of another.

## Existing canonical entrypoints — preserve

- `.github/workflows/repository-freshness.yml`: push-triggered and nightly, **read-only** public SHA/CORS/anonymous-denial drift detection. Keep no Azure credentials, secret reads or resource writes in this lane.
- `.github/workflows/deploy-dev.yml`: existing protected-main backend release mutex `crown-api-dev-deploy`; currently **manual workflow_dispatch only**.
- `.github/workflows/deploy-dashboard.yml`: existing DEV-certification SWA preview deployment; its `dev_deploy_only=true` path must skip CORS mutation, synthetic school fixture writes and live buyer submissions.
- `.github/workflows/dev-blacklist-database-inventory.yml`: separately guarded read-only Azure PostgreSQL inventory, not ordinary image deployment.
- Other reviewed schema stages continue to require exact-owner explicit authority. No new top-level workflows, Azure resources, paid services, or external orchestration platform.

## Mandatory automatic-release gates (not yet implemented or active)

1. **Two-key activation:** a governed source opt-in and a separately verified repository/environment configuration setting. The checked-in default must be OFF; a GitHub variable of unknown provenance must never activate deployment by itself. Owner authorization is required for the first activation and initial controlled DEV release.
2. **Identity and CI:** exact current protected `main` SHA; no historic reruns/RC branch; all 17 configured required checks terminal-green against that source, including tenant/security, release authority, schema and finance gates. Verify source again before each mutation. A stale/moved `main` blocks; never quietly deploy an ancestor.
3. **Database:** the normal code-only path runs the verified `--inspect-all-migrations` connection with `default_transaction_read_only=on` and **zero pending migrations**. Nonzero, unknown, broken schema graph, inconsistent history or unavailable DB blocks automatic deployment. Reviewed schema changes require an independent, owner-authorized migration/recovery window.
4. **Recovery and costs:** verify the prior image digest and previous healthy source can actually be restored, document operator rollback authority and limit work to the existing RG, ACR, App Service and SWA; do not assert a tested restore from backup metadata alone. Preserve the Azure monthly cost target; monitor usage rather than assume $0.
5. **Build then activate:** pin and verify immutable backend image and frontend assets before changing runtime identity; serialize backend deployment under the existing lock, avoid activating a source that lacks its required database schema, and treat rollback/safe-state as a release invariant. Don't write `BUILD_SHA` until its image is available.
6. **Frontend follows backend:** promote the same accepted source to DEV-certification SWA only after the API and artifact build SHAs are healthy and exact. Use only the deployment-only lane for unattended code changes. No synthetic invitations, school provisioning, Jireh writes, payment activation or CORS/CSRF modifications automatically.
7. **Post-deploy proof:** API `build_sha` equals immutable `artifact_build_sha` equals DEV preview `build.json` equals accepted source; database health, DEV environment, anonymous owner denial and preview CORS checked. Separate privileged and buyer/parent persistence tests remain mandatory for *certification*, not automatically green from parity.
8. **Failure behavior:** fail closed, retain sanitized artifacts, do not print tokens/DB URLs, avoid unbounded retries or expensive resource recreation. Preserve previous release when feasible; record precise blocked action in [#687](https://github.com/Arete0920/Crown-CSMS/issues/687) and route hosted certification blockers to [#427](https://github.com/Arete0920/Crown-CSMS/issues/427).
9. **Protection:** no bypass/self-approval, forced updates, branch-rules relaxation or production changes. The `SOLO_DEVELOPER_APPROVED_WORKAROUND` permits governed solo-maintainer source review with compensating CI, **not** an implied Azure/DB mutation approval. Repository tooling is **not approval authority**.

## Implementation stages

- **Stage A — current draft PR #688:** make *manual* DEV deployment fail closed on the **read-only** zero-pending schema gate; build/push immutable image before appsettings. Maintain exact current-main checks; regressions must pass. This is **not** automation and does **not** establish rollback completeness.
- **Stage B — after Stage A proof:** implement and test an opt-in, default-disabled promotion controller using existing canonical workflows. Add positive and negative tests for blocked schema, missing CI/recovery, stale source, wrong environment, prior run state, backend failure, frontend failure and drift already resolved. Verify no extra workflow or unapproved write path.
- **Stage C — separate owner authorization:** first successful manual exact-main DEV backend/frontend release and physical/hosted acceptance as separately scoped; then explicitly activate periodic safe-code delivery under the proven opt-in. Record first auto-run SHA, results and cost; revert the activation switch on any unexpected behavior.

## Current release decision

Until Stage A/B controls are green, Stage C is separately authorized and a complete end-to-end exact-source release is proven: **automatic Azure DEV deployment OFF; hosted buyer certification NO-GO**.

Automatic drift detection already exists. Do not turn a failing freshness check green by skipping it or deploying a source whose schema/runtime authority is uncertain.
