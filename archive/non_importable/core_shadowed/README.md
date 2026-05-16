# core_shadowed

**Status:** ARCHIVED - Do not import

This folder contains a legacy Django app that was renamed to resolve module shadowing issues during test execution.

## Why it's here

In early development, there were two `core` packages on the import path:
- `Crown2026/core/` (repo root)
- `Crown2026/backend/core/` (canonical)

When pytest ran, Python would resolve `import core` to the repo-root version, causing the migration loader to fail with `NodeNotFoundError`.

## The fix

Renamed `core/` → `core_shadowed/` (commit 81523b40) so `import core` now resolves only to `backend/core`.

## What to do with this folder

- **Option 1 (Recommended):** Delete it entirely if it was never used as a live app
- **Option 2:** Rename it to something meaningful (e.g., `legacy_core`, `archived_models`) and remove Django app scaffolding
- **Option 3:** Keep it as-is if there's a future plan to restore it

**For now:** Do not import or reference anything in this folder. It exists only for historical clarity.

---

*Generated: 2026-02-02 | Commit: 81523b40*
