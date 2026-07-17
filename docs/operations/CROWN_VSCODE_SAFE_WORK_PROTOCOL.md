# CROWN VS Code Safe Work Protocol

## Purpose

Use VS Code for controlled local development without broad copy-and-paste changes, unstated assumptions, or unrelated edits.

## Required workflow

### 1. Confirm repository state

From the repository root in PowerShell:

```powershell
git status -sb
git branch --show-current
git rev-parse HEAD
```

Do not begin from an unexplained dirty worktree.

### 2. Define the work boundary

Record:

```text
TASK=<one sentence>
EXPECTED_FILES=<exact paths or directories>
FORBIDDEN_FILES=<protected or unrelated paths>
VALIDATION=<commands that prove the change>
```

Do not edit when the expected files or acceptance criteria are unclear.

### 3. Work in an isolated branch or worktree

Do not commit directly to `main`. Keep one logical change per branch and pull request.

### 4. Edit deliberately

- Inspect the current implementation before changing it.
- Make the smallest change that resolves the verified issue.
- Do not paste large replacement blocks without reviewing every affected line.
- Do not perform unrelated refactors, formatting sweeps, dependency upgrades, or mass renames.
- Do not change authentication, RBAC, tenant enforcement, migrations, production deployment, secrets, package manifests, lock files, or workflows unless explicitly authorized.

### 5. Validate locally

Run focused checks first, followed by relevant broader checks. PowerShell is appropriate for repeatable diagnostics, validation, evidence capture, and repository operations.

At minimum:

```powershell
git diff --check
git diff --name-only
git diff --stat
```

Then run the backend, frontend, contract, security, or browser checks that match the changed behavior.

### 6. Inspect the complete diff

Review every changed file before staging. Confirm that no generated output, local settings, credentials, logs, caches, or unrelated files are included.

### 7. Close the work

The closeout must report:

- branch and HEAD;
- files changed;
- validation commands and results;
- known limitations;
- rollback approach;
- independent-review status.

Do not commit, push, merge, or claim completion while validation is failing, pending, stale, or incomplete.

## Binary rule

No PASS, no commit, no push, and no merge unless the scoped diff and required validation are clean.
