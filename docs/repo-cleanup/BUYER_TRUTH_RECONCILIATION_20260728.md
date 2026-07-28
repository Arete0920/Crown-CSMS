# CROWN Buyer-Truth Reconciliation Record

**Date:** 2026-07-28  
**Branch:** `agent/buyer-truth-reconciliation`  
**Purpose:** Remove confirmed buyer-facing authority conflicts without erasing historical provenance.

## Controlling authority

- Canonical document hierarchy: `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`
- Current release and freeze posture: `docs/CURRENT_RELEASE_STATUS.md`

## Confirmed conflicts resolved

| Document | Verified problem | Resolution |
|---|---|---|
| `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md` | Claimed `ACTIVE — Highest Project Authority`, conflicting with the canonical index | Replaced current-tree body with a superseded historical record; preserved former content by blob SHA |
| `docs/status/PROJECT_COMPLETE.md` | Used current-looking `PROJECT COMPLETE`, `100% COMPLETE`, and production-ready language; contained a stale `AllowAny` example | Replaced with a historical feature snapshot; documented that current source uses `IsAuthenticated` and staff/superuser checks; preserved former content by blob SHA |
| `docs/release/FINAL_PRODUCTION_READINESS_DECISION_PACKET_20260622.md` | Presented June product-scope certification claims without a prominent current supersession boundary | Replaced with a historical NO-GO record; preserved former content by blob SHA |
| `docs/canonical/CANONICAL_DOCUMENT_INDEX.md` | Did not explicitly list the three known conflicting records | Added an explicit superseded-records table and this reconciliation record |

## Source-code verification performed

The current `director_actions` implementation in `backend/crown_api/director_views.py` was inspected through the GitHub connector. It uses `@permission_classes([IsAuthenticated])`, rejects unauthenticated users, and requires staff or superuser access. This confirms that the historical `AllowAny` example was stale documentation, not the current visible implementation.

This source inspection is not a substitute for executable authorization, tenant-isolation, or regression testing.

## Preservation rule

No historical body was represented as destroyed. The former versions remain retrievable from repository history using these blob SHAs:

- Buyer-ready canon: `c3350f5e0df1de4ed6ac43f15066768494e3f349`
- Project-complete snapshot: `a0a3a295fb376d53cf20df878aea790567a02d93`
- June readiness packet: `242e7f9ef2fdb040c5e6b284c2d74705518b36a2`

## Remaining work requiring a full authenticated clone

This reconciliation resolves the confirmed conflicts above. It does not claim a complete repository-wide census. The following still require a working full clone and executable environment:

1. enumerate every completion, readiness, GO, certification, compliance, and buyer-ready claim;
2. resolve inbound links and references to superseded records;
3. classify all historical and generated evidence files;
4. hash and evaluate duplicate evidence packs;
5. scan branches, tags, releases, artifacts, bundles, and retained refs;
6. run broken-link, secret, large-object, dependency, dead-code, and sensitive-data scans;
7. verify executable behavior against the final selected SHA.

## Current disposition

These changes are documentation and diligence corrections only. They do not alter the frozen NO-GO/HOLD posture and do not establish production authorization, buyer readiness, or transfer readiness.
