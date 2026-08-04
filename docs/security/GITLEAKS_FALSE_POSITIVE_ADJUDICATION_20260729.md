# Gitleaks False-Positive Adjudication — 2026-07-29

## Scope

This record adjudicates the 185 `generic-api-key` findings produced by
Gitleaks 8.18.4 during the pre-push scan of the rewritten 335-branch,
279-tag maintenance mirror.

The source report was generated with:

- repository `.gitleaks.toml`;
- repository `.gitleaksignore`;
- `--log-opts=--all`;
- redaction enabled.

No secret value is reproduced in this record or in the source reports.

## Result

All 185 findings were verified as non-secret identifiers or deliberately
inert examples:

| Count | Classification | Evidence |
| ---: | --- | --- |
| 156 | Azure Kudu request-correlation UUIDs | `client-request-id` attributes in 78 Kudu trace XML files |
| 7 | Git commit identities | 40-character source/release authority SHAs in release evidence |
| 4 | Integrity digests | SHA-256 values for `SECRET_SCAN_FINDINGS.txt` in audit-bundle manifests |
| 5 | Public or placeholder application identifiers | Three explicit recovery-script placeholders and two Azure client-ID UUIDs; client IDs are identifiers, not client secrets |
| 4 | Deliberately truncated token example | The same non-functional, ellipsis-terminated JWT example in API documentation |
| 9 | Application/test symbolic keys | Signal rule keys, dashboard role keys, a tenant-test case key, and a CRM API test-fixture key |

No credential, private key, client secret, refresh token, password, or
connection secret was found among these 185 findings.

## Bounded disposition

Each reviewed result is excluded by its complete Gitleaks fingerprint in
`.gitleaksignore`. No Gitleaks rule, path, entropy threshold, workflow, or
required gate is disabled or weakened. A changed commit, path, rule, or line
produces a different fingerprint and remains detectable.

## Validation performed

An isolated transaction mirror was rebuilt from the 335 branches and 279 tags
advertised by GitHub. The rebuild aborted on ref drift and verified:

- 525 authorized rewritten refs;
- 89 unchanged refs;
- rewritten `main` at
  `ddb0a85bc2de62b0ce9832c420a86251547e7110`;
- the forbidden Ed25519 path absent from all retained refs and the reachable
  object listing;
- full `git fsck --no-dangling` passed.

The rewritten all-ref Gitleaks scan produced zero findings with the reviewed
fingerprints. Git reported 10 missing `docx2txt.exe` conversions, so every
reachable DOCX object was independently enumerated and extracted:

- 8 unique reachable DOCX blobs;
- all XML, relationship, text, CSV, and JSON members scanned;
- zero Gitleaks findings;
- temporary extracted content deleted after verification.

## Remaining Lane 4 blockers

This adjudication does not close Lane 4:

1. The known Ed25519 private-key history remediation must still complete under
   the protected-ref maintenance runbook.
2. The final rewritten mirror must repeat the all-ref and reachable-DOCX scans
   after this change is merged into the exact maintenance source identity.
3. Runtime credential inventory, rotation, revocation, failed-rotation
   rollback, and break-glass exercises remain separately required by #1628.

## Review status

`INDEPENDENT_REVIEW_REQUIRED`

## Final current-ref refresh — 2026-08-04

### Evidence basis

Source SHA: `6df9f6b110bfb5584e000366a257efa56ae5617b`. The isolated mirror rewrite removed the exact forbidden Ed25519 path, passed repository and bundle verification, passed full `git fsck`, and restored a verified fresh clone. Predicted rewritten `main`: `fadc86b847c59f5f65c1d3ce43da4d35ff48299e`.

### Re-adjudication result

Every redacted finding was resolved against the rewritten objects. Unknown rules, paths, or structures fail closed.

| Findings | Unique fingerprints | Classification |
| ---: | ---: | --- |
| 234 | 234 | Azure Kudu request-correlation UUIDs |
| 29 | 1 | GitHub check-run and health metadata identifiers |
| 7 | 7 | Git commit and release-authority identities |
| 4 | 4 | SHA-256 integrity digests |
| 2 | 2 | Azure public application/client identifier UUIDs |
| 8 | 8 | Application, test, and documentation symbolic keys |
| **284** | **256** | **Total** |

No credential, private key, client secret, refresh token, password, session secret, connection secret, or signing material was identified. Only exact rewritten fingerprints are added; no detector or scan boundary is weakened.

This refresh does not authorize an authoritative ref rewrite or close Lane 4. A green all-ref and reachable-DOCX preflight, separately authorized ref maintenance, and post-mutation fresh-clone verification remain required.
