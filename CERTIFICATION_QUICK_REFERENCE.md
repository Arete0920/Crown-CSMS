# Audit Bundle Certification: Quick Reference

## Complete Workflow (Copy-Paste Ready)

### Step 1: Generate Runtime Bundle
```bash
cd /workspaces/Crown2026

# Generate deterministic audit bundle with manifest
python solomon_governance_c1/generate_audit_pack.py generate

# Output shows bundle_id (ISO timestamp)
# New files created in: solomon_governance_c1/governance/c1/runtime/audit_pack/[bundle_id]/
```

### Step 2: Certify Bundle
```bash
# Get latest bundle ID
latest=$(cat solomon_governance_c1/governance/c1/runtime/audit_pack/LATEST_BUNDLE.txt)
bundle_path="solomon_governance_c1/governance/c1/runtime/audit_pack/$latest"

# Certify (validates all checks, writes attestation)
python solomon_governance_c1/certify_audit_pack.py "$bundle_path"

# Output:
# ✓ AUDIT_PACK_CERTIFICATION.json (created)
# ✓ AUDIT_PACK_SHA256SUMS.txt (created)
# Status: BUNDLE_CERTIFIED
```

### Step 3: Verify Bundle Integrity
```bash
# Replay verify (full integrity check)
python solomon_governance_c1/verify_audit_pack_integrity.py replay "$bundle_path"

# Output:
# ✓ AUDIT_PACK_REPLAY_VERIFICATION.json (created)
# Status: BUNDLE_REPLAY_VERIFIED
```

### Step 4: Optional - Promote to Canonical AUDIT_PACK
```bash
# Only if certification and replay both PASS
# Requires explicit approval and --force flag

python solomon_governance_c1/generate_audit_pack.py promote \
  --bundle "$bundle_path" \
  --force

# Output:
# Files copied to canonical AUDIT_PACK/
# Original bundle remains in runtime_pack/[bundle_id]/
```

---

## Testing Tampering Detection

```bash
# Add a line to an artifact
echo "TAMPERING" >> "$bundle_path/00_OVERVIEW.txt"

# Try to verify (will fail)
python solomon_governance_c1/verify_audit_pack_integrity.py integrity "$bundle_path"

# Output: INTEGRITY_CHECK_FAILED - TAMPERING_DETECTED: 00_OVERVIEW.txt

# Restore from git
git checkout "$bundle_path/00_OVERVIEW.txt"

# Verify again (will pass)
python solomon_governance_c1/verify_audit_pack_integrity.py integrity "$bundle_path"
# Output: OK
```

---

## Files Generated (Per Bundle)

| File | Purpose | Format |
|------|---------|--------|
| `00_OVERVIEW.txt` | Git branch, HEAD, file counts | Text |
| `01_TREE.txt` - `14_DEPLOY_PROD_RECENT.txt` | Evidence artifacts (13 more) | Text/JSON |
| `99_BUNDLE_MANIFEST.json` | Bundle metadata + SHA-256 hashes | JSON |
| `AUDIT_PACK_CERTIFICATION.json` | Attestation record (NEW) | JSON |
| `AUDIT_PACK_SHA256SUMS.txt` | Hash manifest in standard format (NEW) | Text |
| `AUDIT_PACK_REPLAY_VERIFICATION.json` | Integrity audit trail (NEW) | JSON |

---

## Key Design Principles

1. **Runtime-first** — Bundles generated to runtime/ not committed by default
2. **Explicit certification** — Separate command required, not automatic
3. **Tamper-proof** — Byte-level hash detection, immutable records
4. **Governance gate** — Promotion requires explicit --force after review
5. **Audit trail** — Every step recorded (generation, certification, replay, promotion)

---

## Exit Codes

| Command | Exit 0 | Exit 1 |
|---------|--------|--------|
| `generate_audit_pack.py` | Bundle created | IO error |
| `certify_audit_pack.py` | All checks PASS | Any check FAIL |
| `verify_audit_pack_integrity.py` | All checks PASS | Any check FAIL |
| `generate_audit_pack.py promote` | Promotion done | Blocked (missing cert/approval) |

---

## Checking Bundle Status

```bash
latest=$(cat solomon_governance_c1/governance/c1/runtime/audit_pack/LATEST_BUNDLE.txt)
bundle="solomon_governance_c1/governance/c1/runtime/audit_pack/$latest"

# See all files in bundle
ls -lh "$bundle"/ | grep -v "^d"

# Check certification status
cat "$bundle/AUDIT_PACK_CERTIFICATION.json" | python -m json.tool | grep certification_decision

# Check replay status
cat "$bundle/AUDIT_PACK_REPLAY_VERIFICATION.json" | python -m json.tool | grep replay_decision

# Verify hashes match
sha256sum -c "$bundle/AUDIT_PACK_SHA256SUMS.txt" | head -5
```

---

## Troubleshooting

### Bundle not found
```bash
# Check LATEST_BUNDLE.txt pointer
cat solomon_governance_c1/governance/c1/runtime/audit_pack/LATEST_BUNDLE.txt

# List all bundles
ls -la solomon_governance_c1/governance/c1/runtime/audit_pack/
```

### Certification failed
```bash
# Check exact failure
python solomon_governance_c1/certify_audit_pack.py "$bundle_path"

# Common causes:
# - missing required artifact
# - CRLF line endings (should be LF)
# - unsorted file list
# - hash mismatch (already tampered)
```

### Cannot promote
```bash
# Check prerequisites
[[ -f "$bundle/AUDIT_PACK_CERTIFICATION.json" ]] && echo "✓ certified" || echo "✗ not certified"
[[ -f "$bundle/AUDIT_PACK_REPLAY_VERIFICATION.json" ]] && echo "✓ verified" || echo "✗ not verified"

# Promotion requires both AND --force flag
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIT EVIDENCE LIFECYCLE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GENERATE                CERTIFY               VERIFY            │
│  ────────                ───────               ──────            │
│  generate_audit_pack.py  certify_audit_pack.py verify...py      │
│         ↓                       ↓                    ↓            │
│  runtime_bundle/       + CERTIFICATION.json   + REPLAY.json     │
│  [ISO_TIMESTAMP]/      + SHA256SUMS.txt                         │
│  ├── 00_OVERVIEW.txt                                            │
│  ├── 01_TREE.txt                                                │
│  ├── ...                                                         │
│  ├── 14_DEPLOY_PROD_RECENT.txt                                  │
│  └── 99_BUNDLE_MANIFEST.json                                    │
│                                                                  │
│         RUNTIME_PACK (never auto-committed)                     │
│                                                                  │
│         ↓ (explicit --force after governance approval)          │
│                                                                  │
│  AUDIT_PACK/  ← CANONICAL (immutable, protected)                │
│  ├── [all 15 artifacts]                                         │
│  ├── 99_BUNDLE_MANIFEST.json                                    │
│  ├── AUDIT_PACK_CERTIFICATION.json                              │
│  ├── AUDIT_PACK_SHA256SUMS.txt                                  │
│  └── AUDIT_PACK_REPLAY_VERIFICATION.json                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## See Also

- [CERTIFICATION_ARCHITECTURE.md](CERTIFICATION_ARCHITECTURE.md) — Full design documentation
- [generate_audit_pack.py](solomon_governance_c1/generate_audit_pack.py) — Bundle generation
- [certify_audit_pack.py](solomon_governance_c1/certify_audit_pack.py) — Certification logic
- [verify_audit_pack_integrity.py](solomon_governance_c1/verify_audit_pack_integrity.py) — Verification logic
