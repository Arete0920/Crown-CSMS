# OpenAPI Documentation

This folder contains the exported OpenAPI schema for Crown.

## Canonical Schema File

- `docs/openapi/crown-openapi.yaml`

Status:
- File exists in-repo.
- Currency against latest backend code is `MANUAL_VERIFICATION_REQUIRED` until regenerated and diff-checked.

## Live Documentation Routes

Configured in `backend/crown_api/urls.py`:

- `/api/schema/` (raw OpenAPI schema)
- `/api/docs/` (Swagger UI)
- `/api/redoc/` (ReDoc)

## How to Regenerate Schema

From repository root:

```bash
.venv/bin/python backend/manage.py spectacular --file docs/openapi/crown-openapi.yaml
```

If using Windows PowerShell:

```powershell
& ".venv\Scripts\python.exe" "backend\manage.py" spectacular --file "docs/openapi/crown-openapi.yaml"
```

If repo-root venv is not available, activate your current Python environment and run:

```bash
python backend/manage.py spectacular --file docs/openapi/crown-openapi.yaml
```

## Validation Checklist

1. Regenerate schema.
2. Confirm no unexpected diff in `docs/openapi/crown-openapi.yaml`.
3. Verify `/api/docs/` and `/api/redoc/` load correctly in target environment.
4. Record evidence path in `docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md`.
