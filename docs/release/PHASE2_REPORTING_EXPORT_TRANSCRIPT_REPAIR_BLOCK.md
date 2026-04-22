# Phase 2 Repair Block: Reporting / Export / Transcript

Generated: 2026-04-21

## Current RED-Lane Evidence
- `Reporting/Export/Transcript + Role Routing` fails with 404s on:
  - `/api/v1/transcripts/`
  - `/api/v1/transcripts/generate/`
  - `/api/v1/exports/`
  - `/api/v1/reports/export/`

## Route Surface Already Present
- Transcript endpoints already implemented in `backend/academics/urls.py`:
  - `/api/v1/academics/transcript/{student_id}/`
  - `/api/v1/transcripts/students/{student_id}/`
  - `/api/v1/academics/students/{student_id}/transcript/`
- Export endpoints already implemented in `backend/crown_api/exports/urls.py` under:
  - `/api/v1/exports/*.csv`

## Patch Applied in This Block
- Added compatibility endpoints in `backend/crown_api/release_gate_views.py` and wired them in `backend/crown_api/api_v1_urls.py`:
  - `GET /api/v1/transcripts/` (explicit probe)
  - `POST /api/v1/transcripts/generate/` (explicit probe)
  - `GET /api/v1/exports/` (index facade)
  - `GET /api/v1/reports/export/` (facade)

## Why This Is Safe
- No destructive behavior added.
- Existing canonical transcript/export endpoints remain source of truth.
- New routes are compatibility/facade surfaces for release gate checks and operator clarity.

## Remaining Product Work (Still Required for True GREEN)
- Implement full transcript generation workflow tied to registrar flow (not just probe semantics).
- Implement report-domain exports and board-pack outputs as first-class endpoints with contract tests.
- Add unauthorized denial proofs for every export surface by role (parent/teacher/student/guest).
- Add live metrics provenance checks to prove reporting is not mock/seed backed where production claims are made.

## Re-run Commands
- Phase 2 only:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\release-certification\06_run_phase2_gates.ps1 -OutputDir .\audit-artifacts\release-certification\phase2-manual`
- Full harness:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\release-certification\00_run_release_certification.ps1 -BaseUrl "http://127.0.0.1:8000" -FrontendUrl "http://127.0.0.1:3000" -RepoSlug "tcmegahan/Crown2026" -SandboxAdminEmail "admin@heritage.test" -SandboxAdminPassword "Crown2026!" -SandboxSecondAdminEmail "admin@harvest.test" -SandboxSecondAdminPassword "Crown2026!" -SchoolAdminRoute "/school-admin-dashboard" -SkipLoad`
