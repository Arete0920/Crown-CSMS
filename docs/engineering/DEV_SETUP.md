# CROWN Developer Setup

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Purpose:** One source of truth for local development setup.

This document replaces duplicated local setup instructions in older build, onboarding, and canon documents.

If another document conflicts with this file, this file controls unless a later signed engineering decision explicitly replaces it.

---

## 1. Repository

Clone and enter the repository:

```bash
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026
```

For an existing local checkout, open the repository root in VS Code.

## 2. Python virtual environment

Canonical approach: repo-root `.venv`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

On Windows with PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

**Best practice:** Call the interpreter explicitly in scripts rather than relying on an activated shell:

```bash
./.venv/bin/python backend/manage.py check
```

or on Windows:

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
```

## 3. Frontend dependencies

```bash
cd frontend/dashboards
npm ci
cd ../..
```

## 4. Required local secrets

Copy the local secrets example and fill in local-only values:

```bash
cp local.secrets.example local.secrets
```

**Never commit:**

- passwords
- API keys
- bearer tokens
- refresh tokens
- production `.env` files
- production database dumps
- real student data
- real family data
- real staff data
- real school financial data
- tenant secrets
- private certificates

## 5. Backend checks

```bash
source .venv/bin/activate
python backend/manage.py check
python backend/manage.py migrate
```

Or without activating the environment:

```bash
./.venv/bin/python backend/manage.py check
./.venv/bin/python backend/manage.py migrate
```

## 6. Start backend

```bash
source .venv/bin/activate
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

Backend health check:

```bash
curl -i http://127.0.0.1:8000/health/
```

Expected:

- HTTP 200
- JSON body
- no traceback

## 7. Start frontend

Open a second terminal:

```bash
cd frontend/dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

Frontend health check:

```bash
curl -i http://127.0.0.1:3000/
```

Expected:

- HTTP 200

## 8. Canonical verification commands

Backend fast check:

```bash
source .venv/bin/activate
python backend/manage.py check
pytest backend -m "not integration and not slow"
```

Frontend fast check:

```bash
cd frontend/dashboards
npm run lint
npm run test:unit
npm run test:contracts
npm run build
```

Accessibility release check:

```bash
cd frontend/dashboards
npm run test:release:a11y
```

## 9. Local troubleshooting

Check backend port:

```bash
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr ":8000"
```

Check frontend port:

```bash
# Linux/macOS
lsof -i :3000

# Windows
netstat -ano | findstr ":3000"
```

Kill by PID only when necessary:

```bash
# Linux/macOS
kill -9 <PID>

# Windows PowerShell
taskkill /PID <PID> /F
```

**Do not repeatedly kill all Python or Node processes without checking ports first.**

## 10. Postgres for local data (if needed)

If your local setup requires a database server:

```bash
# Via Docker
docker run -d \
  --name crown-postgres \
  -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=crown_dev \
  -p 5432:5432 \
  postgres:15
```

Update `backend/.env` with:

```
DATABASE_URL=postgresql://<db-user>:<db-password>@127.0.0.1:5432/<db-name>
```

## 11. Day 1 safety note

This file is documentation authority only.

It does not certify:

- pilot readiness
- GA readiness
- production readiness
- compliance completion
- release approval

For production deployment and release decisions, see your engineering leadership.
