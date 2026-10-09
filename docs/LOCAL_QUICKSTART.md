# CROWN Local Quick Start — Windows PowerShell

**Status:** Local development and fictional Heritage demonstration only; not a production or Azure release certification.
**Authority:** [Engineering setup](engineering/DEV_SETUP.md), [current release status](CURRENT_RELEASE_STATUS.md), and exact current GitHub `main`.
**Last reviewed:** October 9, 2026. The documented commands have not been executed on the owner's Windows laptop by this review.

## Choose the correct local workflow

CROWN currently runs locally. No Azure subscription, resource group, cloud database, or deployment credential is needed for the local Heritage demonstration. **Do not mistake successful GitHub CI or an older demo snapshot for proof of local Windows operation.**

Two toolchain contracts coexist:

- **General development:** Python 3.12 and Node.js 20 LTS, as specified in `engineering/DEV_SETUP.md`.
- **Heritage local demonstration launcher:** Python 3.11+ and Node.js **22.12+**, enforced by `scripts/demo/start_heritage_local.py`. Python 3.12 is the tested Python target. Use Node.js 22.12+ for this path; don't assume Node 20 can run the launcher.

Install Git, Python and Node.js using their official installers. Work from a normal writable, **trusted** local directory. PowerShell and the standard Windows command prompt are sufficient; no editor or Azure connection is required.

### A. Rehearse the current-checkout Heritage demo locally

Open **PowerShell** in the CROWN repository root (the folder containing `backend`, `frontend` and `scripts`):

```powershell
git rev-parse HEAD
py -3.12 --version
node --version
npm --version
py -3.12 scripts/demo/start_heritage_local.py --prepare-only
py -3.12 scripts/demo/start_heritage_local.py
```

The launcher creates an isolated local `.venv`, SQLite database, synthetic Heritage records, and frontend build; checks the backend; runs migrations and `sandbox_proof_gate --strict`; and starts backend `127.0.0.1:8000` and frontend `127.0.0.1:4173`. After startup, open `http://localhost:4173/sandbox`. Preserve the console and logs for any failed step. The first preparation needs internet access to download dependencies.

Use **fictional data only**. The passwordless sandbox is for the same computer; do not port-forward it or expose it on a public network. External payment processing is not part of this demo. Do not assume that every optional integration works offline.

If you are starting from an old copied ZIP instead of an active checkout, obtain the intended source first and record its exact SHA. The separate `Start-Heritage.cmd` downloader intentionally pins revision `5e49157f440c549b9394f3cea7259c09d409b6bd`: that historical demo is **not** current-`main` proof. Its existing README documents Linux rehearsal and explicitly states native Windows execution has not been verified.

### B. Validate general source development without launching Azure

For the canonical Python 3.12 / Node 20 development toolchain:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe -m pytest backend -m "not integration and not slow"

Push-Location frontend\dashboards
npm ci
npm run lint
npm run test:unit
npm run test:contracts
npm run build
Pop-Location
```

Run these commands from the repository root. They may take time, and database-dependent tests may require local configuration. A failure is evidence to investigate, not a reason to disable tests or tenant guards. Keep local credentials out of the repository and use `127.0.0.1` loopback for development servers.

The `npm run test:unit`, `test:contracts`, `lint` and `build` scripts are declared in `frontend/dashboards/package.json`. Exact current-head CI is the source verification authority until the same commands actually pass on Windows.

## Local evidence checklist

Record these facts privately for each rehearsal:

1. Full `git rev-parse HEAD` SHA and whether the tree was clean.
2. Windows edition, Python version, Node/npm versions, start command and exit code.
3. Backend `check`, database migration, synthetic seed and sandbox proof outcomes.
4. Frontend build and actual `localhost` HTTP reachability.
5. Authorized administrator/teacher/parent/student workflows, persistence after reload, and negative cross-school/role tests.
6. Failure logs, corrective changes, repeat results and an operator/date acknowledgment.
7. Local-only conclusion; **Azure runtime, production identity, payments, operational backup/restore and independent SOC 2 assurance remain unverified** until separately proven.

## Avoid obsolete instructions

An earlier revision of this quick-start suggested a fixed Azure development school UUID, `core.models.CustomUser`, a legacy `/api/auth/token/` route, `npm install`, and a guaranteed seeded data count. Those instructions were **not verified as a correct current local setup** and must not be followed as release authority. Use the current canonical setup, live role/tenant contracts, and verified demo commands above.

This guide does not delete historical module-specific seed commands; run any such command only after inspecting its current `--help` and verifying a disposable local database. Never use a `--force`/wipe switch on an unbacked-up school database.
