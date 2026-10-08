# BJU Press Scope & Sequence Integration Status

Date: 2026-10-08  
Status: Governed official-source registry implemented; bulk objective ingestion not authorized

## Decision

CROWN/Solomon may use BJU Press official-source metadata to identify curriculum editions, grade bands, subject lanes, and authoritative source links for curriculum mapping and lesson-planning workflows.

CROWN/Solomon must not scrape, mirror, reproduce, or bulk-ingest publisher-owned scope-and-sequence text unless the publisher grants the necessary rights.

## Verified Official Sources

| Academic year | Resource | SKU | Registry posture |
| --- | --- | --- | --- |
| 2026 | Christian School Scope & Sequence | 563213 | Official reference |
| 2027 | Christian School Scope & Sequence | 577536 | Official reference |
| 2026 | Biblical Worldview Scope & Sequence | 563049 | Official reference |
| 2027 | Biblical Worldview Scope & Sequence | 575555 | Official reference |

The 2026 academic scope-and-sequence is a 191-page BJU Press publication organized by subject. Its contents identify these top-level lanes: Early Childhood, Reading/Literature, Writing & Grammar, Spelling, Handwriting, Vocabulary, Math, Science, Heritage Studies, Bible, and Spanish.

## Repository Implementation

- `backend/academics/bju_scope_sequence.py` is the authoritative application registry for approved BJU scope-and-sequence source metadata.
- `backend/academics/tests/test_bju_scope_sequence.py` proves current-year coverage and enforces fail-closed rights behavior.
- `solomon-source-corpus/bju_press_metadata_manifest.csv` records the same sources in Solomon governance metadata.
- Curriculum mapping and lesson-planning code may consume the registry to select the correct publisher/year/source without embedding protected publisher content.

## Current Capability Statement

Implemented:
- BJU publisher recognition.
- 2026/2027 academic source identification.
- 2026/2027 biblical-worldview source identification.
- 2026 official subject-lane index.
- governed source selection for curriculum mapping and lesson-planning surfaces.
- fail-closed objective-ingestion authority.

Not yet implemented:
- complete grade-by-grade objective ingestion.
- complete lesson-by-lesson BJU objective crosswalk.
- automatic generation of BJU-derived lesson content.
- copyrighted source storage inside Solomon.

Those items remain blocked on explicit publisher authorization or a separately documented rights determination.

## Product Rule

Do not describe Solomon as containing the complete BJU Press curriculum or complete BJU Press scope-and-sequence objective corpus until the authorization flag can truthfully be changed and the resulting corpus has passed provenance, coverage, and regression verification.

## CI Verification Note

PR validation must execute the repository's normal required checks on the exact head. A GitHub Actions attempt that terminates before any job step executes is infrastructure evidence, not application-test evidence, and must be rerun rather than bypassed.
