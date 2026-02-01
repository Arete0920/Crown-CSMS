# Line Ending & Encoding Fix Summary

## What was wrong

1. **No `.gitattributes`** - Git used platform defaults, causing CRLF/LF inconsistency
2. **Git `autocrlf=true`** - Git automatically converted line endings, causing confusion
3. **No encoding enforcement** - Files could be created with UTF8-BOM instead of UTF8
4. **No pre-commit validation** - Problems only discovered after push to GitHub

## What we fixed

### 1. `.gitattributes` (forces line endings at Git level)
```
*.yml  text eol=lf     # GitHub Actions requires LF
*.yaml text eol=lf
*.sh   text eol=lf     # Linux containers require LF
*.py   text eol=lf
*.ps1  text eol=crlf   # PowerShell on Windows expects CRLF
```

### 2. Git configuration (stop auto-conversion)
```bash
git config --global core.autocrlf false
git config --global core.safecrlf true
```

### 3. `.editorconfig` (editor-level consistency)
- Forces UTF-8 encoding
- Forces LF line endings for YAML
- 2-space indent for YAML files

### 4. Validation script (`scripts/validate-workflows.ps1`)
- Checks for UTF8-BOM (should be no-BOM)
- Checks for CRLF in YAML (should be LF)
- Validates basic YAML structure
- Checks for tabs (YAML requires spaces)

## How to use

**Before committing workflow changes:**
```powershell
.\scripts\validate-workflows.ps1
```

**Check a specific file for BOM:**
```powershell
$path = ".github\workflows\ops-reset-dev.yml"
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    "BOM found"
} else {
    "Clean"
}
```

**Fix a file with BOM:**
```powershell
$content = Get-Content $path -Raw
[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))
```

## Verification

The workflow now:
- ✅ Shows proper name in `gh workflow list` (not just file path)
- ✅ Accepts `workflow_dispatch` triggers
- ✅ Run 21566267791 completed successfully

## Prevention

1. **`.gitattributes`** enforces at commit time
2. **`.editorconfig`** enforces in editor
3. **`validate-workflows.ps1`** catches before push
4. **`core.autocrlf=false`** stops Git from "helping"
