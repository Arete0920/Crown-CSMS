# COPILOT TASK PROTOCOL (MANDATORY)

## Core Rule
ONE task at a time. NO extra changes. NO assumptions.

## Before Any Change
- Restate the task in one sentence.
- List exact files to be changed.
- If unclear, STOP and ask.

## During Work
- Do not add "helpful" improvements.
- Do not refactor unrelated code.
- Do not touch secrets, passwords, tokens, or env files.
- Do not change PROD behavior unless explicitly instructed.
- Do not invent requirements.

## After Work (Required Report)
- Files changed (list)
- Diffstat (lines added/removed)
- Tests run (exact commands)
- Result (PASS/FAIL)
- Commit SHA

## Safety Stops
- If behavior differs between DEV/PROD: STOP.
- If instructions conflict: STOP.
- If unsure what "done" means: STOP.

## Tooling Rules
- PowerShell: use curl.exe explicitly.
- Prefer Invoke-RestMethod for JSON.
- Never rely on SSH for recovery unless instructed.

## Enforcement
If any rule is violated:
1. STOP
2. git diff --name-only
3. git restore affected files
4. Re-run tests
5. Resume only with explicit instruction
