# Ed25519 history-remediation runbook

## Status and authority

This runbook implements the repository-side preparation for issue #1692. It does not revoke, rotate, generate, register, or distribute a cryptographic key. Those actions require an authorized operator in the system that trusted the exposed key.

Production authorization remains blocked until both operational key retirement and repository-history remediation are independently verified.

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
2. Revoke or retire the exposed key pair in those systems.
3. Generate a replacement key only in an approved secret-management or hardware-backed process.
4. Update downstream trust to the replacement public key.
5. Verify that the retired key can no longer authorize or validate new privileged actions.
6. Retain sanitized evidence: timestamps, fingerprints, affected systems, operator, approver, and verification results. Never commit private key material.

History cleanup cannot substitute for this step.

### 3. Preserve controlled evidence

Before rewriting refs, create one encrypted, access-controlled preservation copy. Record its checksum, custody, and purpose. The preservation copy must remain clearly marked `INTERNAL ONLY - CONTAINS RETIRED PRIVATE KEY MATERIAL`.

### 4. Rewrite distributable history

Perform this operation from a clean maintenance clone with all intended branches and tags fetched. Coordinate a repository maintenance window before changing shared refs.

```bash
git clone --mirror https://github.com/Arete0920/Crown-CSMS.git Crown2026-remediation.git
cd Crown2026-remediation.git

git filter-repo \
  --path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem' \
  --invert-paths \
  --force
```

Do not push immediately. Run all verification steps first.

### 5. Verify the rewritten mirror

Run the repository verifier before any force update:

```bash
./tools/verify_remediated_git_bundle.sh \
  --repo Crown2026-remediation.git \
  --forbidden-path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem'
```

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

Afterward:

- invalidate stale local clones and require a fresh clone;
- replace mirrors, cached archives, bundles, release assets, and downloadable artifacts;
- review forks and external copies where removal is feasible;
- rerun all-ref verification against the authoritative remote.

### 7. Produce the distributable bundle

Create the second bundle only from verified remediated refs:

```bash
git bundle create Crown2026_remediated.bundle --all
./tools/verify_remediated_git_bundle.sh \
  --bundle Crown2026_remediated.bundle \
  --forbidden-path 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem'
sha256sum Crown2026_remediated.bundle
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

Issue #1692 must not close based only on this runbook, a redacted current-tree file, or a green pull request. Closure requires operational retirement of the key, verified rewritten refs, replacement of distributable artifacts, and a clean remediated bundle.