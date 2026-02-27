# Crown2026 Wizard Conventions

## Naming rules

| Layer | Pattern | Example |
|---|---|---|
| Django app name | `<name>_wizard` | `section_assign_wizard` |
| Session model | `<Name>WizardSession` | `SectionAssignWizardSession` |
| URL prefix | `/api/v1/<name>-wizard/sessions/` | `/api/v1/section-assign-wizard/sessions/` |
| Frontend page | `pages/<Name>Wizard.jsx` | `pages/SectionAssignWizard.jsx` |
| Frontend steps dir | `pages/<name>_wizard/` | `pages/section_assign_wizard/` |
| Frontend api module | `api/<name>_wizard.js` | `api/section_assign_wizard.js` |
| Router path | `/<name>-setup` | `/section-assign-setup` |

## State lifecycle (required 6 states)

```
draft → configured → <domain_state_1> → <domain_state_2> → committed → verified
```

- `draft` — session created, nothing set
- `configured` — term/year/basic config saved
- `<domain_state_1>` — first domain-specific data saved
- `<domain_state_2>` — second domain-specific data staged/previewed
- `committed` — idempotent write to production models completed
- `verified` — result confirmed by GET; session frozen

## Endpoint contract (6 endpoints per wizard)

```
POST   /api/v1/<name>-wizard/sessions/                   → 201 { session_id }
POST   /api/v1/<name>-wizard/sessions/{id}/configure/    → 200
POST   /api/v1/<name>-wizard/sessions/{id}/<step3>/      → 200
POST   /api/v1/<name>-wizard/sessions/{id}/<step4>/      → 200
POST   /api/v1/<name>-wizard/sessions/{id}/commit/       → 200 { ...result }
GET    /api/v1/<name>-wizard/sessions/{id}/verify/       → 200
```

## Auth requirements (every endpoint)

```python
authentication_classes = [JWTAuthentication, SessionAuthentication]
permission_classes = [IsAuthenticated]
```

`get_request_school_id(request)` must be called on every endpoint.
Session lookups must use `get_object_or_404(Session, id=..., school__id=school_id)`.

## Wiring checklist (must do for every wizard)

- [ ] `backend/<name>_wizard/` app created with `apps.py`, `models.py`, `views.py`, `urls.py`, `migrations/`, `tests/`
- [ ] `backend/crown_api/settings.py` — app added to `INSTALLED_APPS`
- [ ] `backend/crown_api/urls.py` — URL prefix added
- [ ] `pytest.ini` — test directory added to `testpaths`
- [ ] `frontend/dashboards/src/api/<name>_wizard.js` created
- [ ] `frontend/dashboards/src/pages/<Name>Wizard.jsx` created
- [ ] `frontend/dashboards/src/pages/<name>_wizard/Step1–Step6.jsx` created
- [ ] `frontend/dashboards/src/routes/wizards.js` — entry added to `WIZARD_REGISTRY`
- [ ] `backend/tests/test_wizard_contract.py` — entry added to `WIZARD_ENDPOINTS`
- [ ] `makemigrations <name>_wizard` + `migrate` + `manage.py check`
- [ ] `pytest backend/<name>_wizard/tests/ -v` → all pass
- [ ] `npm run build` → 0 errors

## Commit message format

```
feat: <name> wizard (Wizard #N) — backend + tests X/X + frontend + build
```

## Contract test location

`backend/tests/test_wizard_contract.py` — `WIZARD_ENDPOINTS` list at top of file.
Add one entry when you add a wizard. This test catches: missing URL wiring,
broken auth, broken tenant isolation.

## Frontend registry location

`frontend/dashboards/src/routes/wizards.js` — `WIZARD_REGISTRY` list.
`router.jsx` calls `...wizardRoutes()` and never manually lists wizard routes.
