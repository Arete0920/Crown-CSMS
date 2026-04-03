# Copilot Guardrails - Crown2026 Project

**NON-NEGOTIABLE RULES:**

## 1. Directory & Execution
- **ONLY** work in `c:\Users\JMega\OneDrive\Desktop\Crown2026\backend`
- **ALWAYS** use `.\venv\Scripts\python.exe` (never `python` alone)
- **ALWAYS** use absolute paths in PowerShell: `& "path\to\python" "path\to\manage.py" ...`
- **NEVER** modify root-level files (manage.py, venv, etc.)

## 2. Code Changes (Ask First)
- ❌ Do NOT modify `settings.py`, `urls.py`, or migrations without explicit request
- ❌ Do NOT add new dependencies or install packages
- ❌ Do NOT modify Django auth, admin core, or contrib packages
- ✅ Do modify app-specific code (models, views, admin, forms)
- ✅ Create new feature files only if explicitly requested

## 3. Git Discipline
After ANY change:
```
git status
git diff --name-only
git add <files>
git commit -m "clear message"
git push
```

## 4. Server Management
**Start server ONLY this way:**
```
cd c:\Users\JMega\OneDrive\Desktop\Crown2026\backend
& ".\venv\Scripts\python.exe" "manage.py" runserver 127.0.0.1:8000 --noreload
```

**Test with:**
```
curl http://127.0.0.1:8000/api/director/aid/summary/?school_id=0c0d109f-3752-496b-906b-3b45e16a91fd&year_id=31cf07c5-38ee-4d0d-aef6-e6adb2704d13
```

## 5. Debugging (No Guessing)
If something breaks:
1. `git status` + `git diff` (prove what changed)
2. `.\venv\Scripts\python.exe manage.py check` (Django validation)
3. Run server with `--noreload --verbosity 3` (see actual errors)
4. **Do NOT** clear pycache, reset venv, or modify package.py unless traceback proves it
5. **Do NOT** create debug scripts or test files without user approval

## 6. Commits Must Include
```
git log --oneline -1
# Example: "feat: add director dashboard API endpoints + audit trail"
```

## 7. Final Verification (Before closing)
- [ ] `git status` is clean (no untracked junk)
- [ ] `git log -1` shows commit message
- [ ] Server boots with `--noreload`
- [ ] API endpoint responds with JSON
- [ ] No `.pyc`, `__pycache__`, or `.log` files in git

---

**Current Status (Jan 3, 2026 04:34 UTC):**
- ✅ Server running at http://127.0.0.1:8000
- ✅ API endpoints functional
- ✅ Django checks pass
- ✅ Code is clean (only intentional changes)
