# Buyer history assessment — October 4, 2026

Inspected published main: `af873827c8cec81a29bab01a9d55883091875cd9`.
The clean clone fetched 109 origin tracking refs (including symbolic HEAD). The local scan also included preparation branches. This assessment does not clear distribution.

## Fresh scan

Gitleaks 8.30.1 was obtained from its release and verified against the published SHA-256 checksum. The scan used `gitleaks git --log-opts=--all --redact=100` with the checked-in configuration and existing ignore fingerprints. It exited 1 and reported 71 candidate occurrences: 68 generic-api-key, two curl-auth-header, and one private-key. Counts describe this configuration and ref inventory; they are not an unfiltered count of all historical risks. They are not directly comparable to the earlier isolated rewrite's 88 candidates.

The separate known-path verifier failed for the documented private-key path across retained refs and reachable history. Current-tree placeholders, PR closure and present secret-scan passes do not close that exposure. No private-key bytes were printed, no raw token values were included in this report, and no published refs were rewritten.

## Resolution of the three previously unresolved documentation occurrences

At historical commit `415b4538ed08322db520736edf24f5a3546da59b`, `docs/DAY2_DASHBOARD_ENDPOINTS.md` lines 71, 104 and 142 each assign the same 26-character JWT-looking example to a PowerShell token variable. The literal ends with an ellipsis and fails the three nonempty base64url-segment JWT structure. The accompanying snippets use it as a Bearer example. These three exact occurrences are nonfunctional truncated documentation examples, not complete authentication tokens.

The SHA-256 of the exact quoted example is `01cd93d6f6a5efc6ab3ce7218df68184bdf366eafcbe54da0ca6404bac61fc9f`. This is a metadata-only adjudication of those three occurrences, not proof about other tokens, signing keys, consumers or credentials. No ignore fingerprint or detector exemption is added.

## Remaining prerequisites

- Review the complete current candidate inventory, including curl-auth-header findings, before treating the scan as cleared.
- Identify every consumer of the exposed Ed25519 key and verify retirement and replacement trust. Current source search did not establish that inventory.
- Preserve controlled evidence, prepare and verify a fresh isolated rewrite, and review exact branch/tag changes before owner-authorized shared-ref maintenance.
- Verify authoritative remote refs and replace distributable artifacts; account separately for hidden PR refs, forks, caches and external clones.

The existing source-locked rewrite runner and old approved-candidate manifest are not refreshed by this assessment and must not be used as authorization for the new ref inventory. Follow the [history-remediation runbook](ed25519-history-remediation-runbook.md).
