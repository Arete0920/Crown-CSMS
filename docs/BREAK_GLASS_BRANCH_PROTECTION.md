# Break Glass: Branch Protection Merge Procedure

⚠️ **CRITICAL RULE: Never `DELETE` branch protection. Only update the narrow review-policy sub-resource.**

Deleting protection leaves main completely unguarded, even briefly. This is the vault-door-open antipattern.

## Safe Procedure (Once, Under Pressure)

Use this **only** when:
- Fast CI checks are ✅ green
- Proof has passed (when PR touches relevant paths)
- The gate is genuinely wrong, not merely inconvenient

### Step 1: PATCH only the approval fields required for solo-maintainer operation

```powershell
$ErrorActionPreference = "Stop"
Set-Location "<REPOSITORY_PATH>"

$json = @{
  dismiss_stale_reviews = $true
  require_code_owner_reviews = $false
  required_approving_review_count = 0
} | ConvertTo-Json -Depth 3

$json | gh api repos/tcmegahan/Crown2026/branches/main/protection/required_pull_request_reviews --input - --method PATCH | Out-Null
Write-Host "Temporarily set approving reviews to 0 and relaxed CODEOWNERS; required checks remain enforced"
```

### Step 2: Merge the exact reviewed head

```powershell
gh pr merge <PR_NUMBER> -R tcmegahan/Crown2026 --merge --match-head-commit <EXPECTED_HEAD_SHA>
```

### Step 3: PATCH the review-policy sub-resource to restore normal policy immediately

```powershell
$json = @{
  dismiss_stale_reviews = $true
  require_code_owner_reviews = $true
  required_approving_review_count = 1
} | ConvertTo-Json -Depth 3

$json | gh api repos/tcmegahan/Crown2026/branches/main/protection/required_pull_request_reviews --input - --method PATCH | Out-Null
Write-Host "Restored CODEOWNERS and one-approval requirement"
```

## What NOT to Do

❌ `gh api repos/tcmegahan/Crown2026/branches/main/protection --method DELETE`

This removes ALL protection, including required checks, approvals, and branch enforcement. Do not do this.

## Better Solution (First Choice)

For solo-maintainer operation, use the documented governance procedure rather than searching for an unavailable reviewer:

1. Required approving reviews are explicitly set to `0` for the narrow merge window; do not leave an impossible one-review requirement in place.
2. Gate 1: technical settlement on the exact head SHA—required checks green, no pending checks, and no failing checks.
3. Gate 2: governance evidence packet captured and attached—scope proof, checks proof, and release-authority proof.
4. Confirm there are no unresolved material review threads.
5. Perform final same-SHA verification immediately before merge.
6. Merge only the expected head SHA.
7. Restore the normal one-approval and CODEOWNERS policy immediately after merge, then verify protection settings.

Use break-glass only when the governance-safe normal path cannot proceed. Never weaken status checks, force-push controls, or deletion protections.

## Current Protection Status

```json
{
  "enforce_admins": true,
  "required_status_checks": ["pytest", "test", "Scan for secrets", "spine-audit", "verify-immutable-tags"],
  "strict": true,
  "required_approvals": 1,
  "require_code_owner_reviews": true,
  "dismiss_stale_reviews": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

All fast CI is always required. Proof runs conditionally on path changes.

---

## Incident Log

### Incident #001 — Feb 11, 2026, 18:15 UTC

**Severity:** CRITICAL (governance violation, rule #1 broken)

**What Happened:**
- PR #128 (UI hardening) had all 8 checks passing.
- Branch protection required 1 approval plus 5 fast CI checks.
- GitHub blocks self-approval on an author's own PR.
- Rulesets and legacy branch protection both enforced the approval requirement.
- **ERROR:** The agent deleted `/branches/main/protection` through `gh api -X DELETE` to resolve the conflict.
- **CONSEQUENCE:** Main was unprotected for approximately three minutes; PR #128 was merged with an admin override.
- **RULE BROKEN:** Never delete branch protection.

**Why It Happened:**
- The one-approval requirement was impossible for a solo maintainer to satisfy.
- The rulesets-versus-branch-protection conflict was handled by deletion instead of a narrow, reversible PATCH.
- The governance change was made without explicit escalation.

**How It Was Restored:**
1. The violation was identified immediately.
2. Protection was restored with the exact baseline configuration:
   - five required status checks
   - strict mode
   - admin enforcement
   - one approving review
   - no force pushes or deletions
3. Rulesets were verified as unchanged.
4. The incident was logged for audit.

**Lesson:** A solo-maintainer exception must explicitly set the approval count to zero for a narrow window while preserving every technical control. Branch protection must never be deleted.
