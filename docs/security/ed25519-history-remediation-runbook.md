# Ed25519 history-remediation runbook

## Status and authority

This runbook implements the repository-side preparation for issue #104. It does not revoke, rotate, generate, register, or distribute a cryptographic key. Those actions require an authorized operator in the system that trusted the exposed key.

Production authorization remains blocked until both operational key retirement and repository-history remediation are independently verified.

The [2026-10-12 trust-consumer review](ED25519_TRUST_CONSUMER_REVIEW_20261012.md)
records the bounded repository evidence, public identifiers, missing retirement
receipts and remaining operational/maintenance requirements. Historical audit
metadata still says `ATTESTED` and selects the affected bundle as `active`;
those labels are not current trust authority. Treat that attestation as
untrusted for authorization or new assurance claims pending issue #104
acceptance. The index's simulated revocation of a different bundle is not
retirement evidence for the exposed key.

## Confirmed repository facts

- Historical commit: `efb4f846bc5a743c88be6e4914aeb89e1f4d88a3`
- Historical path:
  `solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem`
- The current `main` tree contains a redacted placeholder at that path. This prevents current-tree use but does not remove the historical blob.
- The pre-remediation bundle anchored at `fbb10fa1b77b55911e35745ebc84e5e1e9d6dbf7` intentionally preserves the historical object and is internal-only.

## Mandatory sequence

### 1. Contain

1. Restrict the original bundle, clones, mirrors, backups, Actions artifacts, and audit exports to authorized internal access.
2. Do not send the original bundle to a buyer, reviewer, escrow provider, or other counterparty.
3. Record all known locations and custodians.

### 2. Retire the exposed key

1. Identify every verifier, signer, attestation process, service, or trust store associated with the corresponding public key.
   Record key identity and fingerprint encoding from trusted public issuance
   records. Do not retrieve or use the exposed private key. A repository-only
   search cannot establish that no external consumer exists; a no-consumer
   disposition requires named operational confirmation and bounded receipts.
2. Revoke or retire the exposed key pair in those systems.
3. Generate a replacement key only in an approved secret-management or hardware-backed process.
4. Update downstream trust to the replacement public key.
5. Verify that the retired key can no longer authorize or validate new privileged actions.
6. Retain sanitized evidence: timestamps, fingerprints, affected systems, operator, approver, and verification results. Never commit private key material.

History cleanup cannot substitute for this step.

### 3. Preserve controlled evidence

Before rewriting refs, create one encrypted, access-controlled preservation copy. Record its checksum, custody, and purpose. The preservation copy must remain clearly marked `INTERNAL ONLY - CONTAINS RETIRED PRIVATE KEY MATERIAL`.

### 4. Rewrite distributable history

Perform this operation from a clean, restricted maintenance clone with all intended branches, tags, and GitHub-advertised pull-request refs fetched. Coordinate a repository maintenance window before changing shared refs. Use `git-filter-repo` **2.47 or later** so `--sensitive-data-removal` can record the affected PR refs and the first changed commits required by GitHub Support.

```bash
git clone --mirror https://github.com/Arete0920/Crown-CSMS.git Crown-CSMS-remediation.git
cd Crown-CSMS-remediation.git

git filter-repo \
  --sensitive-data-removal \
  --path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem' \
  --invert-paths \
  --force

# A bare mirror stores filter-repo metadata here, not under .git/.
test -f filter-repo/changed-refs || { echo "ERROR: missing changed-ref report" >&2; exit 1; }
python - <<'PY'
from pathlib import Path
changed = Path("filter-repo/changed-refs").read_text(encoding="utf-8").splitlines()
affected = sorted(ref for ref in changed
                  if ref.startswith("refs/pull/") and ref.endswith("/head"))
print(f"affected_pull_request_count={len(affected)}")
for ref in affected:
    print(ref)
PY
```

Preserve **sanitized** filter-repo output containing `NOTE: First Changed Commit(s)`, the changed-ref manifest, and any orphaned-Git-LFS notice in restricted evidence. Do not attach or publish the pre-remediation Git objects or raw private-key material. The affected-PR count is the *changed* PR-head count reported by the rewrite, not the total advertised PR-ref count. Compare exact branch/tag/PR names and OIDs immediately before maintenance; re-run the complete preflight if they drift.

Do not push immediately. Run all verification steps first.

### 5. Verify the rewritten mirror

Run the repository verifier before any force update. A `--mirror` clone is a bare repository and contains no working-tree `./tools/` directory. After finishing the rewrite above, return to the parent directory and extract the verifier from the rewritten repository HEAD without exposing historical key contents:

```bash
cd ..
git -C Crown-CSMS-remediation.git show HEAD:tools/verify_remediated_git_bundle.sh > verify_remediated_git_bundle.sh
chmod 700 verify_remediated_git_bundle.sh
./verify_remediated_git_bundle.sh \
  --repo Crown-CSMS-remediation.git \
  --forbidden-path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem'
```

Keep the temporary verifier and all mirror data within the restricted maintenance workspace. Do not copy the unremediated mirror into buyer-distributable locations.

Also run the repository's configured secret scanner across all retained refs. A current-tree scan alone is insufficient.

Required evidence:

- forbidden path absent from every retained ref;
- no reachable object is associated with the forbidden path;
- secret scan passes across all retained refs;
- expected branches and tags are present;
- rewritten HEAD and ref inventory are recorded;
- application and CI tests pass on the chosen rewritten release identity.

### 6. Force-update shared refs

Only the repository owner may authorize this step. Temporarily suspend merges, communicate the maintenance window, and preserve a rollback reference outside the distributable namespace.

Push rewritten branches and tags deliberately. Do not use an unreviewed blanket mirror push if obsolete or preservation refs would reintroduce the object.

Approval must bind the current source identities and exact old/new ref plan.
Check every planned ref for drift immediately before promotion and abort if
any differs. The legacy source-locked rewrite runner is not approval for the
current repository and its authorization checks must not be bypassed. Include
server-controlled PR refs in the disposition plan; coordinate hosting-provider
cleanup when ordinary branch/tag maintenance cannot remove them.

### GitHub-hosted pull refs and cached-object removal

GitHub-controlled `refs/pull/*` references are read-only to ordinary branch/tag pushes. A verified rewrite of `main` and owner-managed refs alone does **not** remove those server references or cached commit views. Following a successful authorized rewrite of every owner-writable affected ref (and confirmation that forks do not retain the exposed material), submit a private request through the [GitHub Support portal](https://support.github.com/) using the documented [sensitive-data removal procedure](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Supply only sanitized evidence:

- repository `Arete0920/Crown-CSMS` and source/rewrite maintenance identities;
- the **affected** PR-head count from `filter-repo/changed-refs`, not the number of all PR refs;
- the `First Changed Commit(s)` emitted by `git-filter-repo --sensitive-data-removal`;
- any orphaned-LFS-object report requested by Support, with controlled handling;
- evidence that owner-managed refs are rewritten and that remaining PR/cached refs are the unresolved GitHub-hosted copies.

Request adjudication of affected PR refs, server garbage collection, and cached views. GitHub Support determines eligibility and may decline assistance when credential rotation sufficiently mitigates the risk. The repository owner must record the Support case identifier, their disposition, and independently verify the resulting authoritative history. Do not claim deletion or completion simply from filing a support ticket.

**Impact:** GitHub notes that affected closed-PR diff views may be lost and commit identities change; freeze merges and notify collaborators before the authorized maintenance window. The legacy source-locked runner is not suitable for the current refs and must not be used as current authorization. The GitHub integration's inability to read protected-branch settings is not proof protections are absent; the owner must inspect those settings independently.

Afterward:

- invalidate stale local clones and require a fresh clone;
- replace mirrors, cached archives, bundles, release assets, and downloadable artifacts;
- review forks and external copies where removal is feasible;
- rerun all-ref verification against the authoritative remote.

### 7. Produce the distributable bundle

Create the second bundle only from verified remediated refs:

```bash
git -C Crown-CSMS-remediation.git bundle create ../Crown-CSMS_remediated.bundle --all
./verify_remediated_git_bundle.sh \
  --bundle Crown-CSMS_remediated.bundle \
  --forbidden-path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem'
sha256sum Crown-CSMS_remediated.bundle
```

Record:

- SHA-256 checksum;
- exact HEAD commit and subject;
- commit count;
- branch, tag, and total-ref counts;
- tracked-file count at HEAD;
- restored working-tree size;
- creation time and operator;
- clean-clone restoration result;
- all-ref secret-scan result;
- proof that the forbidden path is absent.

## Closure boundary

The phase-3 archive script uses `tools/create_verified_git_bundle.py` to reject
known forbidden history before creating an ordinary bundle and to verify the
restored bundle before publication. Any verification or native-command failure
stops that archive path. It is not a substitute for encrypted controlled
preservation, key retirement, all-ref secret scanning or external-distribution
acceptance. Do not use ordinary archive creation to preserve exposed history;
use the separately authorized custody procedure above.

Issue #104 must not close based only on this runbook, a redacted current-tree file, or a green pull request. Closure requires operational retirement of the key, verified rewritten refs, replacement of distributable artifacts, and a clean remediated bundle.
