# Break Glass: Branch Protection Merge Procedure

⚠️ **CRITICAL RULE: Never `DELETE` branch protection. Only `PATCH` specific fields.**

Deleting protection leaves main completely unguarded, even briefly. This is the vault-door-open antipattern.

## Safe Procedure (Once, Under Pressure)

Use this **only** when:
- Fast CI checks are ✅ green
- Proof has passed (when PR touches relevant paths)
- The gate is genuinely wrong (not "I forgot to add a reviewer")

### Step 1: PATCH to relax CODEOWNERS only

```powershell
$ErrorActionPreference = "Stop"
cd "C:\Users\JMega\OneDrive\Desktop\Crown2026"

$json = @{
  required_pull_request_reviews = @{
    dismiss_stale_reviews = $true
    require_code_owner_reviews = $false
    required_approving_review_count = 1
  }
} | ConvertTo-Json -Depth 5

$json | gh api repos/tcmegahan/Crown2026/branches/main/protection --input - --method PATCH | Out-Null
Write-Host "✅ Temporarily relaxed CODEOWNERS (still requires 1 approval + fast CI)"
```

### Step 2: Merge PR

```powershell
gh pr merge <PR_NUMBER> -R tcmegahan/Crown2026 --merge
```

### Step 3: PATCH to restore CODEOWNERS immediately

```powershell
$json = @{
  required_pull_request_reviews = @{
    dismiss_stale_reviews = $true
    require_code_owner_reviews = $true
    required_approving_review_count = 1
  }
} | ConvertTo-Json -Depth 5

$json | gh api repos/tcmegahan/Crown2026/branches/main/protection --input - --method PATCH | Out-Null
Write-Host "✅ Restored CODEOWNERS requirement"
```

## What NOT to Do

❌ `gh api repos/tcmegahan/Crown2026/branches/main/protection --method DELETE`

This removes ALL protection (fast CI, approvals, branch enforcement). Don't do this.

## Better Solution (First Choice)

Instead of "break glass," add a second approver:

1. GitHub UI: Repo → Settings → Collaborators and teams
2. Add trusted account with Write access
3. Have them approve the PR
4. Merge normally without relaxing protection

This is the right way. Use break-glass only in genuine emergencies.

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

All fast CI required always. Proof runs conditionally on path changes.
