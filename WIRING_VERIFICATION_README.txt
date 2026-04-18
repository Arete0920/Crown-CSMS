RUN ORDER

1. Run:
   powershell -ExecutionPolicy Bypass -File .\APPLY_WIRING_VERIFICATION_PACK.ps1

2. Create a branch:
   git checkout -b wiring-proof-2026-04-10

3. Start local stack:
   powershell -ExecutionPolicy Bypass -File .\scripts\verify\start_local_demo_stack.ps1

4. In a new terminal, run full verification:
   powershell -ExecutionPolicy Bypass -File .\scripts\verify\run_wiring_verification.ps1

WHAT THIS PACK VERIFIES

- Django sanity and migrations
- frontend route/link wiring
- tenant isolation pytest suite
- golden path pytest suite
- local /api/health/ or /api/system/health/
- local /api/docs/ and /api/schema/
- browser login and critical dashboard route smoke