# Runtime Bundle Retention Governance

**Date:** May 15, 2026  
**Status:** IMPLEMENTED  
**Principle:** Append-Only Evidence Preservation

## Core Governance Rule

**Runtime bundles are append-only artifacts.**

Never:
- Mass-delete historical bundles
- Mutate previously certified bundles
- Regenerate over prior certified bundle IDs
- Destroy audit lineage

Instead:
- New bundle ID → new certification → optional supersession metadata
- Preserve complete audit history
- Track supersession and revocation chains

## Why This Matters

Before (Incorrect):
```
generate_bundle_1 → certify → promote → delete_bundle_1 → generate_bundle_2
                                        (history lost)
```

After (Correct):
```
generate_bundle_1 → certify → track_active
                                    ↓
                          generate_bundle_2 → certify → supersede_bundle_1
                                                        (history preserved)
```

## Implementation

### SUPERSESSION_INDEX.json

Tracks complete bundle lifecycle:

```json
{
  "active_bundle": "20260515T182250Z",
  "certified_bundles": [
    {
      "bundle_id": "20260515T181936Z",
      "status": "revoked",
      "revoked_reason": "tampering detected during audit replay",
      "superseded_by": "20260515T182250Z"
    },
    {
      "bundle_id": "20260515T182250Z",
      "status": "active"
    }
  ],
  "superseded_bundles": [
    {
      "bundle_id": "20260515T181936Z",
      "superseded_by": "20260515T182250Z",
      "reason": "replaced by newer certified bundle"
    }
  ],
  "revoked_bundles": [
    {
      "bundle_id": "20260515T181936Z",
      "reason": "tampering detected during audit replay"
    }
  ]
}
```

### manage_bundle_lifecycle.py

Script to govern bundle state transitions:

```bash
# Mark bundle as certified and active
python manage_bundle_lifecycle.py certified \
  --bundle 20260515T182250Z \
  --reason "new generation, supersedes prior bundle"

# Mark bundle as revoked (integrity failure)
python manage_bundle_lifecycle.py revoked \
  --bundle 20260515T181936Z \
  --reason "tampering detected"

# Show current lifecycle status
python manage_bundle_lifecycle.py status
```

## Bundle Lifecycle States

```
┌─────────────────────────────────────────────────────────┐
│         BUNDLE LIFECYCLE STATE TRANSITIONS              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  GENERATED → CERTIFIED → ACTIVE                         │
│                              ↓                          │
│                         SUPERSEDED                      │
│                              ↓                          │
│                          (preserved)                    │
│                                                         │
│  CERTIFICATION FAILED → REVOKED (never promoted)        │
│  TAMPERING DETECTED → REVOKED (after promotion)         │
│  INTEGRITY FAILURE → REVOKED (with reason)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### State Meanings

| State | Meaning | Action |
|-------|---------|--------|
| GENERATED | Created by generator | Awaiting certification |
| CERTIFIED | Passed all validation checks | Eligible for promotion |
| ACTIVE | Currently in-use bundle | Replace by promoting new bundle |
| SUPERSEDED | Replaced by newer certified bundle | Preserved for audit trail |
| REVOKED | Integrity/tampering issue detected | Quarantined, not usable |

## Governance Guarantees

### Never Deleted
```bash
# ✗ NOT ALLOWED
rm -rf runtime/audit_pack/20260515T181936Z/

# ✓ CORRECT
python manage_bundle_lifecycle.py revoked \
  --bundle 20260515T181936Z \
  --reason "integrity failure"
```

### Supersession Tracking
```bash
# When bundle_2 becomes active:
# - bundle_1 automatically marked as superseded
# - supersession_chain preserved
# - bundle_1 still readable in runtime/
# - lineage query possible from SUPERSESSION_INDEX.json
```

### Revocation Immutable
Once marked as revoked:
- Cannot be unmarked
- Reason recorded permanently
- Audit trail includes revocation timestamp
- Cannot be promoted to canonical AUDIT_PACK

## Audit Lineage Query

```bash
# Current active bundle
cat runtime/audit_pack/LATEST_BUNDLE.txt

# Complete lifecycle history
cat runtime/audit_pack/SUPERSESSION_INDEX.json | python -m json.tool

# All bundles (append-only)
ls -1d runtime/audit_pack/202605*/
```

## Storage Model

All bundles preserved in runtime directory:

```
runtime/audit_pack/
├── 20260515T181641Z/    ← First generated bundle (38M)
│   ├── 00_OVERVIEW.txt
│   ├── ... (15 artifacts)
│   ├── 99_BUNDLE_MANIFEST.json
│   ├── AUDIT_PACK_CERTIFICATION.json
│   └── AUDIT_PACK_SHA256SUMS.txt
├── 20260515T181936Z/    ← Second bundle, now revoked (38M)
│   ├── [same structure]
└── 20260515T182250Z/    ← Current active bundle (38M)
    ├── [same structure]
└── SUPERSESSION_INDEX.json  ← Governance record (1KB)
└── LATEST_BUNDLE.txt       ← Current bundle pointer (20B)
```

Total storage: ~114MB for complete audit history (3 bundles × 38MB each)

## Governance Principles Implemented

1. ✓ **Append-only preservation** — bundles never deleted
2. ✓ **Immutable history** — revocation reasons timestamped
3. ✓ **Audit trail integrity** — supersession chain tracked
4. ✓ **Governance accountability** — every state change recorded
5. ✓ **Replay capability** — historical bundles remain readable

## Future Enhancements (Phase 3+)

- Cryptographic signing of SUPERSESSION_INDEX.json
- Multi-party approval for bundle revocation
- Append-only ledger for state transitions
- Immutable governance ledger backend (merkle tree / blockchain)

---

**Key Distinction:**

Evidence is no longer **disposed of when replaced**.  
Evidence is **preserved as archived state** with explicit governance markers.

This transforms the system from "auto-refreshed audit files" to **"immutable governed evidence history."**
