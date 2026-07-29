# OpenAPI Documentation

This folder contains generation and validation instructions for the CROWN OpenAPI schema.

## Source of truth

The backend source and `backend/crown_api/settings.py` define the API schema. Generated schema exports are review artifacts and must not be treated as current unless regenerated from the exact source commit.

## Live documentation routes

Configured in `backend/crown_api/urls.py`:

- `/api/schema/` — raw OpenAPI schema
- `/api/docs/` — Swagger UI
- `/api/redoc/` — ReDoc

## Generate a schema

From repository root:

```bash
.venv/bin/python backend/manage.py spectacular --file /tmp/crown-openapi.yaml
```

Windows PowerShell:

```powershell
& ".venv\Scripts\python.exe" "backend\manage.py" spectacular --file "$env:TEMP\crown-openapi.yaml"
```

Or from an activated Python environment:

```bash
python backend/manage.py spectacular --file /tmp/crown-openapi.yaml
```

## Validation

1. Generate the schema from the exact source commit under review.
2. Confirm generation completes without warnings or exceptions.
3. Review the generated artifact for intended API changes.
4. Verify `/api/docs/` and `/api/redoc/` in the target environment.
5. Retain release evidence outside the active source tree or in the approved workflow artifact store.

Do not commit generated schemas solely as static evidence. Current source and the exact-commit generation result remain authoritative.
