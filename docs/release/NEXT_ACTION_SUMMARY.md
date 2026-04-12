# NEXT ACTION SUMMARY

1. Run freeze reconciliation script:
   - `powershell -ExecutionPolicy Bypass -File scripts/release/29_reconcile_after_freeze.ps1`
2. Verify missing inventory:
   - `Get-Content audit-artifacts/freeze-reconcile/02_missing_files.csv`
3. Run restore chain in order:
   - `powershell -ExecutionPolicy Bypass -File scripts/release/fix_15_to_green.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/fix_16_31_to_green.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/fix_32_46_to_green.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/fix_47_61_to_green.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/28_run_next_release_sequence.ps1`
4. Run verification chain:
   - `powershell -ExecutionPolicy Bypass -File scripts/release/27_schema_green_pass.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/20_release_verify.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/25_build_ship_candidate.ps1`
   - `powershell -ExecutionPolicy Bypass -File scripts/release/26_release_doctor.ps1`
