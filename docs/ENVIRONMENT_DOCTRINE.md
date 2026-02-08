# Crown2026 Environment Doctrine (Lock)

## Canonical Python Version
- Local dev and CI must use Python 3.12.x
- Python 3.13.x is not supported due to dependency wheel availability (notably psycopg2-binary).

## Canonical Virtual Environment
- Use the repo-root venv: C:\...\Crown2026\.venv
- Create it explicitly with Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Canonical Test Invocation

Always invoke pytest through the repo venv interpreter:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest
```

## Expected Skips and Integration Preconditions

Some tests are expected to skip unless these are true:
- The local API server is running (when required by that test).
- CROWN_DEMO_PASSWORD is set for the session (when required by that test).

Example:

```powershell
$env:CROWN_DEMO_PASSWORD = "your_value_here"
```

## Rule

If Python is not 3.12.x, stop and fix the environment. Do not compile wheels to force a pass.
