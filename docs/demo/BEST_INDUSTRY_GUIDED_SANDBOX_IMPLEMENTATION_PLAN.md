# Best-Industry Guided Sandbox Implementation Plan

Date: 2026-05-30
Branch: feature/best-industry-guided-sandbox-20260530

## Purpose

This plan stages the CROWN sandbox program as a controlled, proof-backed implementation instead of a raw open trial.

The target buyer experience is:

```text
/sandbox
  -> choose track
  -> choose guided or self-guided
  -> choose role
  -> one-click launch
  -> short-lived sandbox session
  -> role dashboard with command center
```

Normal evaluators should not handle email/password credentials. Operator fallback credentials may remain available behind `/login` for internal QA only.

## Scope

### Connector-safe work

The following work can be committed through the GitHub connector:

- Add a backend `sandbox_demo` app.
- Add sandbox catalog, invite, session, event, and feedback APIs.
- Add one-click sandbox session creation using short-lived CROWN JWTs.
- Add Heritage Christian Academy flagship seed/reset/proof management commands.
- Add frontend `sandboxApi.js`.
- Replace the buyer-facing `/sandbox` launcher with one-click persona launch.
- Update `SandboxCommandCenter` to use stored sandbox session context and feedback submission.
- Add frontend test coverage for no-password persona launch.
- Add operator runbook and proof instructions.

### VS Code/runtime work

The following must be run locally or in CI because it requires execution:

```powershell
cd backend
python manage.py migrate
python manage.py sandbox_seed_flagship --reset
python manage.py sandbox_proof_gate --strict
```

```powershell
cd ..\frontend\dashboards
npm test -- sandbox
npm run build
```

Then perform browser smoke proof:

```text
/sandbox
  -> Head of School
  -> Finance Director
  -> Parent
  -> Teacher
  -> feedback submission
```

## Required release gates before external self-guided use

| Gate | Required result |
| --- | --- |
| `/sandbox` renders | PASS |
| One-click persona launch creates JWT session | PASS |
| No evaluator-facing password fields on `/sandbox` | PASS |
| Heritage seed creates expected records | PASS |
| Reset restores expected records | PASS |
| Head, Admissions, Finance, Teacher, Parent, Student sessions work | PASS |
| Dashboard command center shows role/school/scenario context | PASS |
| Feedback works and blocks prohibited real-data patterns | PASS |
| Invite expiration/revocation works | PASS |
| Tenant isolation negative tests pass | PASS |
| Frontend build passes | PASS |
| Backend checks/tests pass | PASS |

## Launch posture

Until proof gates pass, this remains suitable for:

- internal review
- facilitated investor demo rehearsal
- controlled sales-led demo

It is not suitable yet for broad self-guided external buyer access.

## Operator language

Use this wording:

> CROWN does not drop school leaders into an empty sandbox. We provide a guided proof environment using fictional Heritage Christian Academy data so each evaluator can inspect the product from the role that matters to them.

## Implementation pack

The generated implementation pack is named:

```text
crown_best_industry_sandbox_pack.zip
```

Apply it from the repository root with:

```powershell
Expand-Archive .\crown_best_industry_sandbox_pack.zip -DestinationPath .\_sandbox_pack -Force
powershell -ExecutionPolicy Bypass -File .\_sandbox_pack\scripts\execution\230_apply_best_in_industry_sandbox_pack.ps1
```

After applying, run the proof commands above before merging or exposing the sandbox externally.
