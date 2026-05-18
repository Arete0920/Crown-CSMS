# PR #823 Solo-Maintainer Governance Exception Audit Note

Repository: tcmegahan/Crown2026  
Pull Request: #823  
Title: fix: clear CodeQL JS/TS parse-skip warning  
Date: 2026-05-18  
Owner: TC / Founder / Product Owner  
Status: Exception authorized for this PR only

## 1. Purpose

PR #823 normalizes invalid TypeScript export identifiers in ten remediation marker files so CodeQL JS/TS parse-skip warnings can be cleared.

## 2. Scope

This exception applies only to PR #823.

Changed files:

- src/51x51-remediation/administrator-portal-no-placeholder-fake-sample.ts
- src/51x51-remediation/crm-marketing-suite-no-placeholder-fake-sample.ts
- src/51x51-remediation/emergency-medical-essentials-no-placeholder-fake-sample.ts
- src/51x51-remediation/grade-levels-no-placeholder-fake-sample.ts
- src/51x51-remediation/mission-metrics-no-placeholder-fake-sample.ts
- src/51x51-remediation/notifications-framework-no-placeholder-fake-sample.ts
- src/51x51-remediation/parent-portal-no-placeholder-fake-sample.ts
- src/51x51-remediation/portrait-of-the-graduate-no-placeholder-fake-sample.ts
- src/51x51-remediation/shared-design-system-no-placeholder-fake-sample.ts
- src/51x51-remediation/survey-sentiment-engine-no-placeholder-fake-sample.ts

## 3. Governance Issue

Branch protection required at least one approving review from a different write-access reviewer.

The repository is currently solo-maintained. GitHub does not allow the PR author to approve their own pull request.

Therefore, the review requirement was operationally impossible to satisfy without either:

1. adding another write-access reviewer, or
2. using a documented solo-maintainer exception.

## 4. Verification Before Merge

Before the exception was used:

- PR existed.
- PR was open.
- PR was mergeable.
- PR was not draft.
- Workflow checks were reviewed.
- Required checks were not intentionally disabled.
- The PR was narrow and remediation-only.
- No GA, pilot approval, or production-readiness claim was made.

Evidence files:

- 01_pr823_before.json
- 02_branch_protection_before.json
- 03_required_reviews_before.json

## 5. Exception Action

The required approving-review setting was temporarily reduced only to allow PR #823 to merge under the solo-maintainer operating model.

Required status checks and security gates were not intentionally disabled.

## 6. Merge Action

PR #823 was merged using squash merge.

Merge subject:

fix: clear CodeQL JS/TS parse-skip warning (#823)

Merge body:

Normalize identifiers in 10 remediation marker files to clear CodeQL JS/TS parse-skip coverage warnings. Solo-maintainer governance exception documented because branch protection required a non-author approving reviewer.

## 7. Protection Restoration

Immediately after merge, branch protection was restored.

Required evidence:

- 04_pr823_after.json
- 05_branch_protection_after.json
- 06_required_reviews_after.json
- 07_main_after_merge.txt

## 8. Release Boundary

This exception closes only the PR #823 merge blocker.

It does not authorize:

- GA;
- unrestricted pilot;
- production release;
- compliance approval;
- Azure runtime approval;
- backup/restore approval;
- founder acceptance.

Current allowed posture remains:

CONTROLLED SANDBOX ONLY / PILOT-CANDIDATE PREPARATION

## 9. Closure Criteria

This exception is closed only if all are true:

- PR #823 is merged.
- main is refreshed locally.
- branch protection is restored.
- required review policy is restored or replaced by approved solo-maintainer policy.
- before/after evidence is preserved.
- Stage 2 evidence is rerun against refreshed main.

## 10. Final Status

Status: PENDING until after-state evidence confirms merge and protection restoration.
