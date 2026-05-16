# core_shadowed archive

Status: Archived, non-importable reference only.

This directory preserves the former root-level legacy Django app that previously existed near active code.

Do not import from this directory.

Canonical active Django core app is:

- backend/core/

If a future change attempts to recreate a root-level `core/` package, it must be rejected because it can shadow `backend/core` during Python import/test execution.

This archive is retained only for historical traceability.
