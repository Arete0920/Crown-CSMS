# Solo-Maintainer Branch Protection Policy

> Authority Scope Notice (2026-05-29)
>
> This document is a governance policy artifact and not a controlling repository-level release authority source.
>
> Current controlling release-authority sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Status: Active Governance Policy  
Repository: tcmegahan/Crown2026  
Applies to: main branch  
Owner: TC / Founder / Product Owner  
Version: 2026.05

## 1. Purpose

CROWN is currently operated as a solo-maintainer repository. The repository must preserve strong engineering verification without requiring an impossible second human reviewer when no independent write-access reviewer is available.

This policy defines the approved solo-maintainer branch protection model for CROWN.

## 2. Governance Principle

GitHub must remain the primary engineering gatekeeper for:

- pull request workflow
- required status checks
- test gates
- build gates
- secret scanning
- dependency scanning
- CodeQL/security analysis
- release verification
- branch protection
- merge discipline

GitHub does not replace:

- Azure runtime proof
- deployed environment verification
- backup/restore proof
- founder/product-owner acceptance
- legal/compliance approval
- customer/pilot authorization
- production GO/NO-GO authority

## 3. Required Main Branch Protections

The `main` branch must maintain these protections:

| Control | Required Setting |
|---|---|
| Direct pushes to main | Not allowed except emergency admin recovery |
| Pull request workflow | Required where supported |
| Required status checks | Enabled |
| Secret scan | Required |
| Dependency scan | Required |
| CodeQL/security analysis | Required where configured |
| Backend tests | Required |
| Frontend build/tests | Required |
| Release verification | Required |
| Force pushes | Disabled |
| Branch deletion | Disabled |
| Conversation resolution | Preferred where practical |
| Linear history / squash merge | Preferred |

## 4. Required Review Policy

Because CROWN is currently solo-maintained:

| Setting | Approved Solo-Maintainer Configuration |
|---|---|
| Required approving reviews | 0 |
| Self-approval requirement | Not applicable |
| Non-author approval | Not required unless a second trusted reviewer exists |
| Code owner approval | Optional / future state |

This is not a lowering of engineering standards. It is an alignment of governance rules to the actual operating model.

## 5. Required Compensating Controls

When required approving reviews are set to 0, the following controls are mandatory:

1. All required GitHub checks must pass before merge.
2. PR description must clearly explain scope and risk.
3. Security-sensitive PRs must preserve scan evidence.
4. Release-impacting PRs must update or reference an evidence artifact.
5. No PR may claim GA, pilot approval, or production readiness without release-authority proof.
6. Any solo-maintainer merge that modifies governance, security, compliance, tenant isolation, billing, or release gates must include an audit note.

## 6. Exception Path

If branch protection temporarily blocks a necessary merge because it requires a second reviewer that does not exist, the solo maintainer may use a temporary documented exception only if:

1. the PR is narrow in scope;
2. required status checks are green;
3. before-state branch protection is captured;
4. the exception reason is documented;
5. review requirement is temporarily relaxed only as needed;
6. the PR is merged;
7. original protection is restored immediately;
8. after-state protection proof is captured;
9. the exception is committed or preserved in audit artifacts.

## 7. Prohibited Actions

The following are not allowed under this policy:

- disabling required status checks to force a merge;
- disabling secret scan to force a merge;
- disabling CodeQL/security checks to force a merge;
- force-pushing to main;
- deleting branch protection;
- using the exception path for convenience;
- using document edits alone to claim score improvement;
- claiming GA or pilot approval from GitHub checks alone.

## 8. Release Authority Boundary

GitHub green checks mean engineering verification passed.

They do not mean:

- Azure is verified;
- backups/restores are verified;
- compliance is approved;
- founder acceptance is signed;
- controlled pilot is approved;
- GA is approved.

Release authority remains separate and must be decided through the current CROWN release decision process.

## 9. Current Approved Posture

Until all release-authority blockers are closed with durable proof, the allowed posture remains:

CONTROLLED SANDBOX ONLY / PILOT-CANDIDATE PREPARATION

## 10. Future State

When a second trusted write-access reviewer is available, the repository may restore:

- required approving reviews: 1
- require approval from someone other than the author
- code-owner review for sensitive paths

Until then, the solo-maintainer model is the correct governance configuration.
