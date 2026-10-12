# Repository reference-language sweep — 2026-10-12

Decision owner: CROWN repository owner. Scope: all tracked files at base
`91a81f2b0180290802231dca23905cde745daf1e`.
Authority: `PUBLIC_LANGUAGE_POLICY.md`. Rollback: revert this change.

Inspected all 5,043 tracked paths and file contents: 5,033 UTF-8 text files
and 10 binary files. Case-insensitive searches covered authoring-tool and
provider names, model abbreviations, drafting attribution, and method terms.
Binary contents were checked for named references; arbitrary compressed-byte
abbreviation matches were not treated as language. No rendered-image OCR was
performed. No tracked document archives required text extraction.

Neutralized two tool-name mentions in the current cross-conversation policy.
Its limits on automatic conversation access and memory synchronization remain
explicit. No runtime code, applied migrations, dependencies, or controls changed.

## Preserved exceptions

| File or record | Reason |
| --- | --- |
| `docs/release/LIVE_REPORTING_EXPORT_AUDIT.json` | One obsolete task-protocol path in a historical export inventory; changing it would falsify the inventory. |
| Four `01_TREE.txt` files under `solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T*/` | Historical inventories at 181641Z, 181936Z, 182250Z, and 185051Z; six named-reference matches each. |
| `frontend/dashboards/public/brand/kairos.png` | Signed media provenance contains 19 provider-name matches; retain provenance under the public language policy. |
| `frontend/dashboards/package-lock.json` | Five funding URLs ending in `/sponsors/ai`; third-party maintainer attribution, not product language. |

No other named-reference or method-term findings were detected by the sweep.
This result concerns the inspected tracked tree, not prior commits, branches,
external services, or proof that no automated methods were used.

Validation: repeat tracked-tree search, review the one-paragraph diff, run
repository identity/naming hygiene and competitor-name hygiene, and check diff
whitespace. Governed merge remains subject to checks on the resulting PR head.

## Owner-authorized extension

On 2026-10-12 the owner authorized cleanup of the preserved exceptions.
Retired the five obsolete generated inventories listed above as whole records,
rather than editing historical paths. Originals remain at commit
`89f293b580010e49e91951cf0cba0bf34bff4b77`. The reporting audit script can
regenerate its JSON output from the current tree; the deleted inventory is
not current evidence. The table above describes the initial sweep only.

Replaced the signed raster scheduling logo with a newly authored SVG using
the same crown, clock, compass, navy/gold palette, name, and tagline. Updated
the scheduler reference. The original media and its intact provenance remain
in version history. This replacement intentionally changes the artwork.

Removed five optional sponsor links from package funding metadata. Verified
that every non-funding package field remains identical, including licenses,
versions, integrity hashes, and dependency relationships. Other funding and
required attribution remain intact. The removed URL names a maintainer; it
was not evidence of an automated authoring method.

A repeat named-reference scan of the resulting tracked tree found no remaining
named authoring-tool/provider references. This does not rewrite Git history.
