# Branch Protection Setup Guide

**CRITICAL**: CI workflow exists but is NOT enforced until branch protection configured.

## Required Setup (GitHub UI)

### 1. Navigate to Branch Protection
```
Repo → Settings → Branches → Branch protection rules → Add rule
```

### 2. Configure Protection for `main`

**Branch name pattern**: `main`

#### Required Settings (Enforcement)

✅ **Require a pull request before merging**
- Ensures all changes go through PR review
- No direct pushes to main

✅ **Require status checks to pass before merging**
- Select: `gitleaks` (from secret-scan.yml job name)
- This makes the secret scan **required** (not optional)

✅ **Require branches to be up to date before merging**
- Prevents merging stale branches
- Reduces merge conflicts

✅ **Require review from Code Owners**
- Enforces CODEOWNERS file (.github/CODEOWNERS)
- Security files require @tcmegahan review

✅ **Include administrators**
- **CRITICAL**: Without this, admins can bypass all rules
- Ensures security applies to everyone

#### Optional (Recommended)

☑ **Require conversation resolution before merging**
- All PR comments must be resolved

☑ **Require linear history**
- Prevents merge commits, forces rebase or squash

☑ **Require deployments to succeed before merging**
- If you have deployment checks

### 3. Verify Configuration

**Test**: Open PR #43 (or any PR) → Checks tab

Expected:
- ✅ `gitleaks` check appears
- ✅ Shows as "Required"
- ❌ Cannot merge if check fails
- ❌ Cannot bypass even as admin (if "Include administrators" enabled)

---

## Additional Branch Rules

### For `develop` branch (if used)

Apply same rules as `main`:
- Branch name pattern: `develop`
- Enable all required checks
- Require status checks: `gitleaks`

### For `release/*` branches

```
Branch name pattern: release/*
Same protections as main
```

---

## Verification Checklist

After configuring:

- [ ] PR shows `gitleaks` as required check
- [ ] Try to merge PR with failing check → Should block
- [ ] Try to push directly to main → Should block
- [ ] Try to edit .gitleaks.toml without CODEOWNER → Should require review
- [ ] Admin user cannot bypass (if "Include administrators" enabled)

---

## GitHub Secret Scanning (Additional Layer)

**Location**: `Settings → Security → Code security and analysis`

Enable:
- ✅ **Secret scanning** (detects secrets in code)
- ✅ **Push protection** (blocks pushes with secrets, if available)
- ✅ **Dependabot alerts** (detects vulnerable dependencies)
- ✅ **Dependabot security updates** (auto-PRs for security fixes)

**Result**: CI + GitHub push protection = belt + suspenders

---

## CODEOWNERS Enforcement

**File**: `.github/CODEOWNERS`

**Protected files**:
- `.github/workflows/secret-scan.yml` → @tcmegahan
- `.gitleaks.toml` → @tcmegahan
- `.gitleaksignore` → @tcmegahan
- `scripts/Redact.psm1` → @tcmegahan
- `scripts/Invoke-SecureCommand.ps1` → @tcmegahan
- Security-related scripts/configs → @tcmegahan

**Behavior**:
- PRs touching these files require @tcmegahan approval
- Prevents accidental security degradation
- Enforces review of ignore file changes (false positives)

---

## False Positive Workflow

**File**: `.gitleaksignore`

**Process** (when gitleaks flags false positive):

1. Run detailed scan:
   ```bash
   gitleaks detect --report-format json --report-path gitleaks-report.json
   ```

2. Review report, identify false positive

3. Add exclusion to `.gitleaksignore`:
   ```
   <commit-sha>:<rule-id>:<file-path>
   ```

4. Create PR with `.gitleaksignore` change

5. **CODEOWNER review required** (@tcmegahan must approve)

6. After merge, rerun secret scan to verify exclusion works

**Warning**: Never add real secrets to ignore file. Rotate instead.

---

## Emergency Break-Glass

**Scenario**: Critical hotfix needed but secret scan failing

**DO NOT**: Use `--no-verify` or disable checks

**DO**:
1. Fix the secret (rotate, remove, redact)
2. If false positive, add to `.gitleaksignore` with CODEOWNER review
3. If truly urgent, temporarily disable branch protection (Settings → Branches)
4. **Immediately re-enable** after merge
5. Document incident and rotate any exposed credentials

---

## Monitoring & Maintenance

**Weekly**:
- Review `.gitleaksignore` for stale entries
- Check GitHub Security → Secret scanning alerts
- Verify branch protection still enabled

**Monthly**:
- Review CODEOWNERS membership
- Audit secret scan failures (false positives vs real exposures)
- Update gitleaks patterns in `.gitleaks.toml` if needed

**Post-Incident**:
- Follow `ROTATE_SECRETS.md` runbook
- Review how secret was exposed
- Add additional patterns to `.gitleaks.toml` if needed
- Update documentation with lessons learned

---

## Common Issues

**"Check not showing as required"**
- Verify job name in branch protection matches workflow (`gitleaks`)
- Check workflow is on `main` branch (protection applies to merged code)
- Wait ~5 minutes for GitHub to index new workflow

**"Admin can still bypass"**
- Ensure "Include administrators" is checked in branch protection
- This is commonly overlooked but critical

**"CODEOWNERS not enforcing"**
- Verify "Require review from Code Owners" enabled in branch protection
- Verify `.github/CODEOWNERS` file exists and has correct syntax
- CODEOWNERS must be on default branch to take effect

**"Secret scan failing on false positive"**
- Add to `.gitleaksignore` with CODEOWNER review
- Format: `<commit>:<rule>:<file>`
- Do NOT add real secrets to ignore file

---

## References

- CI Workflow: `.github/workflows/secret-scan.yml`
- Gitleaks Config: `.gitleaks.toml`
- False Positives: `.gitleaksignore`
- Code Owners: `.github/CODEOWNERS`
- Rotation Runbook: `ROTATE_SECRETS.md`

**Golden Rule**: If secret scanning blocks legitimate code, fix the scan (add to ignore). If it blocks a real secret, rotate the secret.
