# Crown Final Release Truth Directive

## Effective Immediately
This file is the controlling release-truth standard for Crown.

## Final Production-Ready Release Means
The agreed release scope is:
- fully shipped
- fully tested
- fully evidenced
- fully supportable
- free of demo-only substitutions
- free of partial/incomplete areas inside scope
- free of deferred items inside scope
- free of manual patching or demo-only bypasses on critical flows

## Hard Rules
1. No release claim unless every claimed area is fully shipped and evidenced.
2. No module is "done" unless it meets the full done definition.
3. Any item that is demo-only, partial, deferred, unproven, or manually patched is OUTSIDE the final production-ready release claim.
4. Investor language cannot weaken release truth.
5. TC is the final authority on release-scope truth.

## Prohibited Release Language for Final Release
Do not use these phrases to describe final production-ready release:
- credible MVP
- demo-ready
- pilot-ready
- partial
- deferred
- smallest credible slice
- investor-demo-ready
- bounded remaining work
- production-hardening in progress

## Allowed Language for Final Release
Use only:
- final production-ready release
- fully complete within agreed scope
- fully shipped and evidenced
- release gate green
- no undocumented product gaps
- no demo-only exceptions
- no deferred items inside scope

## Decision Rule
If any meaningful workflow or module inside the claimed release scope still requires:
- defer wording
- pilot wording
- demo wording
- workaround explanation
- manual patching
then the release is NOT final production-ready.

## Required Evidence
Every final release claim must have:
- green test proof
- tenant/RBAC proof where relevant
- deploy/release proof
- artifact path
- owner
- date verified

## Approval
Release truth owner: TC
Technical gate owners: Dev 1 and Dev 5
This directive overrides weaker planning, sprint, and investor-framing language for final release truth.
