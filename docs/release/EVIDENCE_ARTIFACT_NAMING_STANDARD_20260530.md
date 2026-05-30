# Evidence Artifact Naming Standard (2026-05-30)

Purpose: enforce consistent evidence artifact naming for discoverability and automation.

## Standard Pattern

- File name pattern: `<AREA>_<SUBJECT>_<YYYYMMDD>[optional_suffix].<ext>`
- Allowed extensions: `.md`, `.json`, `.txt`, `.csv`, `.ps1`
- Allowed characters in filename stem: `A-Z`, `a-z`, `0-9`, `_`, `-`

## Examples

- `FULL_COMPLETION_EXECUTION_BOARD_20260530.md`
- `MODULE_CERTIFICATION_MATRIX_20260530.md`
- `verify_certification_matrices.ps1`

## Policy

- New release evidence artifacts must conform to this standard.
- Active evidence packet index entries must reference conforming filenames.
- Non-conforming historical files may remain, but must not be added as new active canonical artifacts without normalization.
