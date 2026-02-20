# Crown2026 – Copilot Guardrails (MANDATORY)

You are assisting in a production Django codebase.

STRICT RULES:
- DO NOT invent base classes, mixins, or abstractions.
- DO NOT reference classes unless they already exist and are imported.
- DO NOT add models, fields, or files unless explicitly requested.
- DO NOT partially patch files when asked to replace them.
- When fixing errors, prefer FULL FILE REPLACEMENT over incremental edits.
- DO NOT add future-phase features to MVP code.
- DO NOT use placeholder names or speculative patterns.
- DO NOT introduce TimeStampedModel, AbstractBaseModel, or similar unless instructed.

MVP PHILOSOPHY:
- Minimum viable, boring, deterministic code only.
- Explicit > clever.
- Simple > abstract.
- Correct > complete.

If unsure, STOP and ASK.

This alone dramatically reduces “creative” damage.
# Crown2026 AI Coding Agent Instructions

## 🏗️ Project Architecture

- **Single workspace, Django backend is authoritative.** No sub-projects or microservices; all business logic flows through the Django backend in `backend/crown_api/`.
- **Major API:** The Director Actions API (`POST /api/director/actions/`) is the central pattern for admin actions (see [backend/crown_api/director_views.py](backend/crown_api/director_views.py) and [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md)).
- **Gold Standard Reference:** Financial Aid/Awards code is the canonical pattern; Admissions and Finance modules clone this structure (see [docs/REFERENCE_MODULE_PATTERN.md](docs/REFERENCE_MODULE_PATTERN.md)).
- **No external dependencies, migrations, or config changes unless explicitly approved.** All dependencies must be standard or already present.

## 🚦 Critical Developer Workflows

- **Build/Run:**  
  - The venv lives at the **repo root** (`.venv/`), not inside `backend/`:
    ```
    & ".venv\Scripts\python.exe" "backend\manage.py" runserver 127.0.0.1:8000 --noreload
    ```
- **Testing:**  
  - Automated: `python test_director_actions.py`
  - Manual: `source curl_examples_director_actions.sh` (see examples in file)
- **Git Discipline:**  
  - After any change:  
    ```
    git status
    git diff --name-only
    git add <files>
    git commit -m "clear message"
    git push
    ```
  - Commit early & often, use `{type}: {description}` format (e.g., `feat: director API endpoints`).

## 📚 Project-Specific Conventions & Patterns

- **No changes to auth, roles, finance, or core Django files without explicit approval.**
- **Views and API endpoints use atomic transactions and per-award error handling.**  
  - Example: [director_actions() in backend/crown_api/director_views.py](backend/crown_api/director_views.py#L462)
- **Extensible by gold standard cloning:**  
  - New persona APIs should copy the Financial Aid pattern exactly—see [docs/REFERENCE_MODULE_PATTERN.md](docs/REFERENCE_MODULE_PATTERN.md).
- **Documentation-first:**  
  - Key guides: [README_DIRECTOR_ACTIONS.md](README_DIRECTOR_ACTIONS.md), [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md), [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md), [CHECKLIST.md](CHECKLIST.md), [MASTER_SUMMARY.md](MASTER_SUMMARY.md), [FILE_INDEX.md](FILE_INDEX.md).
- **Quick lookup for any task:**  
  - Find code/tests/examples in [FILE_INDEX.md](FILE_INDEX.md)
  - API specs/examples: [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md)
  - Automated/manual testing: [test_director_actions.py](test_director_actions.py), [curl_examples_director_actions.sh](curl_examples_director_actions.sh)

## 🔗 Integration Points

- **Frontend integration:** Use instructions/examples from [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Cross-component communication:** Always route via Django APIs; never direct DB or file access.

## 🛡️ Guardrails

- **NEVER modify root-level files (`manage.py`, `venv`, etc.)**
- **NO speculative refactors or new dependencies.**  
- **Always verify changes in dev before pushing to prod.**
- **Do NOT add endpoints under `crown_api/api_urls.py` for modules that have their own app URLs.** Use app `urls.py` only (e.g., `financial_aid/urls.py`, `admissions/urls.py`). Legacy routes in `crown_api/api_urls.py` shadow and block new app endpoints.

---

_If any section is unclear or missing key project details, please provide feedback so this guide can be improved for future agents._
