# CROWN Parallel Module Start Runbook — Historical Record

**Status:** HISTORICAL / SUPERSEDED  
**Original date:** 2026-06-10  
**Superseded:** 2026-07-20  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md`  
**Current review authority:** `docs/product/CROWN_MODULE_REVIEW_RACI.md`

## Historical purpose

This file preserves the June 10, 2026 module-first startup approach. It is retained for chronology and must not be treated as the current development workflow, reviewer assignment, approval path, certification process, or release authority.

The original process assigned named operational lanes to TC Megahan, ChatGPT, VS Code, GitHub, and GitHub Copilot. That tooling-specific structure is no longer controlling. Current work must follow the repository's human-ownership, provenance, RACI, PR hygiene, and release-authority controls.

## Current authority correction

- TC Megahan is the Founder/Product Owner and accountable human decision owner.
- AI systems and automated tools may assist with inspection, implementation, testing, analysis, drafting, and evidence organization.
- AI systems and automated tools are not human contributors, independent reviewers, approvers, acceptance authorities, certification authorities, or release authorities.
- A qualified independent reviewer must be a person who did not author the work and whose review is retained.
- Where independent review is unavailable, `SOLO_DEVELOPER_APPROVED_WORKAROUND` provides bounded founder verification but is not independent review, self-approval, or production authorization.
- Current-head CI and evidence remain mandatory where required.
- Production remains not approved unless the controlling release record explicitly says otherwise.

## Retained module-first principles

The following principles remain valid unless superseded by a more specific current control:

1. Modules first.
2. Dashboards second.
3. Certification last.
4. Registry coverage is not completion.
5. Page rendering is not workflow proof.
6. Sample or template data is not production proof.
7. Screenshots and automated findings are supporting evidence, not independent approval.
8. No merge, certification, promotion, or release claim may exceed the retained evidence.

## Current controlled startup sequence

1. Confirm the current branch, exact head SHA, remote alignment, and worktree status.
2. Read `AGENTS.md`, `docs/CURRENT_RELEASE_STATUS.md`, the module canon, completion matrix, data-ownership matrix, permission matrix, dashboard-fit matrix, and review RACI.
3. Define one bounded module or control lane.
4. Inventory relevant models, migrations, services, APIs, permissions, tenant controls, frontend routes, tests, runtime dependencies, and evidence.
5. Identify unsupported claims, duplicate truth, missing wiring, stale records, and blockers.
6. Make the smallest coherent change set on an isolated branch.
7. Run relevant local or connector-backed validation.
8. Push the complete branch and open a draft pull request.
9. Require exact-head checks and resolve actionable review findings.
10. Merge only under the repository's current human-authority and branch-protection controls.

## Module evidence questions

Before a module advances beyond schema-visible or mapped status, answer with retained evidence:

1. Which models and migrations define it?
2. Which services, APIs, serializers, or schemas expose it?
3. Which frontend routes and workflows use it?
4. Which roles and action-level permissions protect it?
5. Which tenant boundaries and direct-access tests protect it?
6. Which tests prove successful and failure behavior?
7. Which audit, export, retention, rollover, and sensitive-data rules apply?
8. Which downstream modules and dashboards depend on it?
9. Which runtime evidence is current and tied to the evaluated SHA?
10. Which gaps block certification or release use?

## Historical tooling references

Any earlier references in repository history to Copilot review, ChatGPT review, VS Code review, Claude review, Grok review, or another automated review path describe assistance or historical process only. They do not establish human authorship, independent review, approval, certification, or release authority.

## Non-approval statement

This historical runbook does not approve production release, sandbox launch, any module, any dashboard, or any current implementation. Current decisions must use current-head evidence and the controlling authority documents.
