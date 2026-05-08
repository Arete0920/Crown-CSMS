# Crown VS Code Safe Work Protocol

## Purpose

Prevent VS Code/Copilot/agent work from wandering, guessing, assuming, hallucinating, or breaking unrelated Crown functionality.

## Required Workflow

### 1. Start guarded session

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\122_crown_guarded_agent_session.ps1 -Mode Start -WorkItem "50 Wizard Deep Dive"
```

### 2. Give VS Code/Copilot only bounded instructions

Use this prompt:

You are working under Crown guarded mode.
Task: Complete only the 50 Wizard Deep Dive assessment/fix item I specify.
Rules:
- Do not guess.
- Do not infer missing code.
- Do not change unrelated files.
- Do not refactor.
- Do not delete files.
- Do not touch Azure, GitHub settings, secrets, auth, RBAC, tenant enforcement, migrations, package manifests, lock files, or workflows unless explicitly authorized.
- Before editing, list exact files you will change.
- After editing, run the Crown guarded close script.
- If evidence is missing, stop and report a blocker.
Allowed output:
- audit artifacts
- wizard matrix updates
- fix queue updates
- targeted wizard files explicitly approved

### 3. Close guarded session

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\122_crown_guarded_agent_session.ps1 -Mode Close
```

### 4. Do not commit unless Close passes

If the close script reports forbidden changes, revert or review before continuing.

## Binary Rule

No PASS, no commit, no push, no merge unless the guard script and validation artifacts are clean.
