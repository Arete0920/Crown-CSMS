# Environment Guard: Fail-Fast Repository Validation

**Status:** ✓ COMPLETE  
**Date:** 2026-05-15  
**Layer:** Defensive Environment Validation

## Problem Addressed

During governance operations, silent environment drift can cause:
- Scripts running in wrong repository
- Operations on wrong branch
- Path mismatches (e.g., `/workspacesCrown2026` typo)
- Undetected Python version mismatches
- Required directories missing

**Solution:** Fail-fast environment validation before ANY governance operation.

## Implementation

### 1. env_guard.py

**Location:** `solomon_governance_c1/env_guard.py` (458 lines)

**Validates:**
- Repository root detection (walks directory tree, validates `.git` and `README.md`)
- Crown2026 repository confirmation (checks git remote for `tcmegahan/Crown2026`)
- Required directory structure:
  - `solomon_governance_c1/`
  - `solomon_governance_c1/governance/c1/runtime/audit_pack/`
  - `.github/workflows/`
  - `backend/`, `frontend/`
- Git state:
  - Valid git repository
  - Current branch detection
  - HEAD SHA validation
  - Branch sanity (warns on non-standard branches)
- Python environment:
  - Python 3.10+ required
  - Required stdlib modules: json, subprocess, pathlib, hashlib, argparse

**Key Functions:**
- `find_repo_root()` → walks up tree, returns Crown2026 root or None
- `validate_repo_root()` → fail-fast if not in repo
- `validate_required_directories()` → fail-fast if structure incomplete
- `validate_git_state()` → fail-fast if git invalid
- `validate_python_environment()` → fail-fast if Python too old
- `validate_environment()` → runs all checks, returns context dict
- `@guard` → decorator for adding validation to functions

**Exit Codes:**
- 0: All validations pass
- 1: Any validation fails (fail-fast)

### 2. Integration into Governance Scripts

All four governance scripts now call `validate_environment()` at start of `main()`:

**certify_audit_pack.py:**
```python
from env_guard import validate_environment

def main() -> int:
    validate_environment()  # ← Fail-fast before certification
    parser = argparse.ArgumentParser(...)
    ...
```

**verify_audit_pack_integrity.py:**
```python
from env_guard import validate_environment

def main() -> int:
    validate_environment()  # ← Fail-fast before verification
    parser = argparse.ArgumentParser(...)
    ...
```

**manage_bundle_lifecycle.py:**
```python
from env_guard import validate_environment

def main() -> int:
    validate_environment()  # ← Fail-fast before lifecycle ops
    parser = build_parser()
    ...
```

**generate_audit_pack.py:**
```python
from env_guard import validate_environment

def main() -> int:
    validate_environment()  # ← Fail-fast before generation
    parser = build_parser()
    ...
```

## Behavior

### Normal Execution (Correct Environment)

```bash
$ python solomon_governance_c1/certify_audit_pack.py --bundle runtime/audit_pack/20260515T182250Z/
✓ Environment valid
  Repository: /workspaces/Crown2026
  Branch: solomon/start
  HEAD: ab41b8aa710e...
[Certification proceeds...]
```

### Fail-Fast (Wrong Environment)

```bash
$ cd /tmp && python /workspaces/Crown2026/solomon_governance_c1/certify_audit_pack.py
FAILED: Crown2026 repository root not found
This script must be run from within the Crown2026 repository
[Exit code 1]
```

```bash
$ cd /workspaces && python Crown2026/solomon_governance_c1/certify_audit_pack.py
FAILED: Required directories not found:
  - /workspaces/solomon_governance_c1
  - ...
[Exit code 1]
```

## Validation Results

```
✓ Environment guard compiles successfully
✓ All governance scripts compile with env_guard integration
✓ Environment validation passes in correct directory
✓ Environment guard detects missing repo root
✓ Environment guard detects incomplete directory structure
✓ Environment guard validates branch state
✓ Environment guard checks Python version
✓ Scripts proceed only after validation passes
```

## Architecture Layer

This adds a **0-layer** to the governance stack:

| Layer | Component | Purpose |
|-------|-----------|---------|
| 0 | `env_guard.py` | **Fail-fast environment validation** (NEW) |
| 1 | `generate_audit_pack.py` | Deterministic generation |
| 2 | `certify_audit_pack.py` | Bundle certification |
| 3 | `verify_audit_pack_integrity.py` | Integrity verification |
| 4 | `manage_bundle_lifecycle.py` | Bundle lifecycle governance |
| 5 | Runtime/canonical isolation | Evidence lifecycle management |
| 6 | `SUPERSESSION_INDEX.json` | Immutable governance records |

## Benefits

1. **Prevents Silent Drift** → Fails immediately if environment is wrong
2. **Deterministic Paths** → All scripts use validated root, no typos
3. **Clear Error Messages** → Operators see exactly what's wrong
4. **Fail-Fast Principle** → No operations proceed in wrong state
5. **Auditable Validation** → All checks logged before any action
6. **Reusable Guard** → Can be extended to validate other preconditions
7. **Zero Performance Cost** → Validation runs once per invocation

## Usage Patterns

### Pattern 1: Direct Import
```python
from env_guard import validate_environment

def my_governance_operation():
    env = validate_environment()
    root = env['root']
    runtime_pack = env['runtime_pack']
    # Proceed with guaranteed valid paths
```

### Pattern 2: Decorator
```python
from env_guard import guard

@guard
def my_governance_operation(env):
    root = env['root']
    # Automatic validation
```

### Pattern 3: Standalone Check
```bash
python solomon_governance_c1/env_guard.py
# Validates and reports environment state
```

## Future Extensions

The env_guard framework enables additional validations:
- Branch-specific operation rules (e.g., only main for promotions)
- Artifact presence checks (e.g., verify AUDIT_PACK/ exists)
- Permission checks (e.g., verify write access to runtime/)
- Configuration validation (e.g., verify cspell.json exists)
- External service checks (e.g., verify git connectivity)

## Implementation Notes

- **Import handling:** Uses try/except for both direct and relative imports
- **Path calculation:** `Path(__file__).resolve().parent` ensures absolute paths
- **Git validation:** Uses `git` CLI, not libgit2 (ensures all environments have git)
- **Fail-fast design:** First validation error causes immediate exit (exit code 1)
- **No side effects:** Validation reads only, never modifies state

## Operational Handoff

**For developers:** Every governance script now validates environment before proceeding.

**For CI/CD:** Environment guard ensures scripts fail safely if run in wrong context.

**For auditors:** Validation logs provide proof that environment was verified before each operation.
