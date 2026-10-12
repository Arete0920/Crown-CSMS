# Ed25519 trust-consumer review — 2026-10-12

Status: **REPOSITORY REVIEW COMPLETE; OPERATIONAL RETIREMENT UNVERIFIED**.
Issue: [#104](https://github.com/Arete0920/Crown-CSMS/issues/104).
Authority: [history-remediation runbook](ed25519-history-remediation-runbook.md).

## Evidence boundary

Reviewed source: `018578f5ad08f076bae2d7445dfa154fa6078234`.
Historical attestation source: `3d587623505b6106c5132947287db2bd12a1e822`.
This is a bounded source review, not an operational inspection or an all-ref
secret scan. A full ordinary clone supplied reachable branch/tag history;
hidden server refs, external consumers, forks, caches and distributed copies
were not inventoried. No private-key blob was opened, printed or used. The
clone contains historical objects and must stay out of distributable artifacts.

Searches used `git grep` over tracked files, including ignored tracked audit
files, for `ed25519`, `AUDIT_PACK_MANIFEST`, `crypto_attestation` and the public
key's encoded body. The body matched only `ed25519_public_key.pem` in the
reviewed current and historical attestation trees. Code review additionally
covered signing, verification and certification implementations. This does
not prove absence of dynamically configured or out-of-repository trust.

All audit-pack paths below are relative to
`solomon_governance_c1/governance/c1/runtime/audit_pack/`.

## Established dependencies

| Consumer or dependency | Repository evidence | Established conclusion |
| --- | --- | --- |
| Audit-pack attestation | `20260515T185051Z/crypto_attestation/CRYPTOGRAPHIC_ATTESTATION.json` | Declares Ed25519, manifest, public-key and signature filenames; still says `ATTESTED`. This is recorded metadata, not newly verified signature evidence. |
| Attestation payload | `20260515T185051Z/crypto_attestation/AUDIT_PACK_MANIFEST.json` | Lists digests/sizes of audit exports and certification records. Identifies what the signature purportedly attests. |
| Audit evidence selection | `SUPERSESSION_INDEX.json` | Selects bundle `20260515T185051Z` as `active` and duplicates the `ATTESTED` claim/public-key and signature references. A documented selection dependency exists. No current executable Ed25519 consumer was located. |
| Historical signer/verifier | Attestation files and historical attestation commit | Signature/public-key files and a commit-level verification claim exist. No committed implementation of the Ed25519 signing or signature-verification operation was located in the reviewed trees. Identity, execution receipt and external implementation remain unknown. |
| C1 certification/determinism | `solomon_governance_c1/certify_audit_pack.py`, `verify_c1_artifact_diff.py` | SHA-256 file comparison/certification; neither establishes Ed25519 key retirement or signature trust. |
| Wallet pass signing | `services/wallet/apple-pass-service/server.js` | Uses supplied P12 certificate, Apple trust certificate and OpenSSL CMS. No dependency on this audit-pack Ed25519 public key was located. |
| Application credentials/payment intents | `backend/crown_api/jwt_utils.py`, `backend/crownpass/credentials.py`, `backend/finance/api_views.py` | HMAC/Django signing based on application secret configuration; no located audit-pack key dependency. Live configuration is unverified. |
| Microsoft identity verification | `backend/core/auth/aad_jwt.py` | RS256 verification using Microsoft JWKS; no located audit-pack Ed25519 dependency. |
| Payment-provider integration | `backend/payments/providers/__init__.py` | Returns a deferred gateway. No implemented trust dependency on this key was located; this does not certify payment-provider readiness. |
| Security gates and maintenance | `.github/workflows/codeql.yml`, `tools/verify_no_tracked_private_keys.py`, `tools/verify_remediated_git_bundle.sh` | Detect forbidden material/history and enforce boundaries. They do not consume the public key to authorize runtime actions. Fixture success is not retirement evidence. |
| Distribution | Runbook preservation bundle, historical audit exports, reachable Git objects | The forbidden path remains tracked as a placeholder and the original commit remains an ancestor of reviewed HEAD. History-bearing clones/bundles can carry the original object. External recipients and copies remain unverified. |

## Public identifier and association limits

The audit-pack public key can be identified without reading a private key:

- SHA-256 of exact committed PEM bytes:
  `d20b43de562810f71cfd7cf4c079a2448b73c0b313b5a331df003563750bdba4`.
- SHA-256 of decoded SubjectPublicKeyInfo DER:
  `1f18877a7792d694f8b5b0fa69cf1d5fdea6cf61967b006df117aea95c02110a`.

These are distinct encodings; evidence must name which it uses. The attestation
metadata itself has a placeholder `public_key_sha256`, not either digest.
Association with the exposed private-key path follows the runbook and shared
audit-pack location. Cryptographic pair correspondence was not tested. An
authorized operator must confirm key identity from trusted issuance/custody
records; do not retrieve or exercise the exposed private key to do so.

## Existing evidence and missing proof

| Existing record | What it supports | What it does not support |
| --- | --- | --- |
| Current redacted private-key placeholder | Current-tree containment at the named path | Historical removal, destruction, revocation or replacement trust |
| `SUPERSESSION_INDEX.json` simulated revocation | Simulation for older bundle `20260515T181936Z` | Retirement of the public key or of active bundle `20260515T185051Z` |
| `GITLEAKS_FALSE_POSITIVE_ADJUDICATION_20260729.md`, including August refresh | Recorded isolated rewrite/scan rehearsals at old source identities | Current authoritative ref cleanup or operational key retirement |
| PR #203 verifier contracts | Rejection of incomplete/masked local history | External trust-store inspection, all-ref secret-scan acceptance or clean distribution |
| `SECRETS_ROTATION_AND_BREAK_GLASS_RUNBOOK.md` and secret-store evidence example | Procedures and evidence shape | An executed, approved retirement event for this key |
| Issue #104 comments | Prior bounded repository review and unresolved requirements | Independent operational receipts |

No completed key-specific operational retirement/replacement receipt was
located in the reviewed records. Historical `ATTESTED`/`active` labels must
not be accepted as current security authority. Treat this attestation as
**untrusted for authorization or new assurance claims pending issue #104
acceptance**. This restriction does not edit historical records, revoke a
live credential, or invalidate the underlying files' independent usefulness.

## Remaining operational acceptance

The authorized security operator must supply a sanitized record with:

1. Key identity/encoding and confirmed association, incident/change ID,
   environment, named operator/approver and UTC timestamps.
2. Each signer, verifier, trust store, evidence selector and distribution
   recipient reviewed; configuration/audit receipt references and disposition.
   If no external consumers exist, record the systems searched, method, scope
   and accountable confirmation. Repository search alone is insufficient.
3. Evidence that old trust is disabled and cannot authorize new actions. Use
   approved test fixtures/receipts, never the exposed private key. Disposition
   of previously signed evidence must be explicit; a compromised signing key
   cannot establish when an untrusted signature was created.
4. Replacement public identifier, custody/issuance receipt, affected trust
   updates and positive/negative verification results where a consumer needs
   replacement. If a consumer is permanently decommissioned, document that
   approved disposition instead of silently claiming replacement.
5. Encrypted preservation-copy checksum, access controls and custodian;
   location references only, with no raw credentials or private material.

## Remaining repository maintenance and distribution

The repository owner must authorize a concrete **current** exact-ref plan and
maintenance window only after operational acceptance and controlled evidence
preservation. Inventory advertised and hidden PR refs, retained/deleted refs,
branch protections, forks and copies. Record source identities and old/new
ref mappings; abort on any ref drift before promotion. The source-locked
`Invoke-AuthorizedEd25519HistoryRewrite.ps1` runner's old base/path restriction
is not authorization for current refs and must not be bypassed.

Under that separately authorized plan: verify the isolated candidate using
the existing history verifier, all-retained-ref secret scanning and reachable
embedded-document scanning/adjudication; preserve intended refs and run
applicable release/CI checks. Then verify authoritative remote refs and a fresh
clone. Resolve server-controlled refs/caches with the hosting provider where
necessary; record external-copy limits honestly. Replace/restrict stale
bundles, archives, release assets, Actions artifacts, mirrors and clones.
Restore and scan a new distributable bundle and record its checksum, exact
release identity and ref inventory. None of these maintenance operations was
performed by this review. Issue #104 remains open.

## Local validation

The six real-Git verifier contract tests passed, Bash syntax validation passed,
and the tracked private-key guard passed on the reviewed source. Running the
unchanged history verifier against the review clone returned exit 1: the
forbidden path exists in retained refs and reachable history. That expected
rejection confirms the blocker; it is not remediation success. These local
checks do not replace applicable exact-head PR checks or operational evidence.

## Exact scanner adjudication

PR run 38313332428 reported one `generic-api-key` finding at lines 49–50
of this review in commit `f101476a3138f02aa6ea192dd3e69df51d3fa1db`.
The candidate is the SHA-256 digest of public SPKI DER bytes documented above,
recomputed from the committed public PEM; it is not a credential or private
material. The redacted SARIF identifies this exact file, rule, commit and
start line. Only that complete history fingerprint is excluded in
`.gitleaksignore`; no rule, directory, scan scope or private-key check changes.
A changed commit/path/rule/line remains detectable. The failed initial run is
preserved as evidence; the corrected PR head requires a new passing scan.
