# Required Controls on `main`

**Status:** current configuration specification
**Repository:** `Arete0920/Crown-CSMS`
**Operating model:** solo maintainer with automated compensating controls

## Pull request policy

- Require a pull request before merge.
- Required approving reviews: **0** while CROWN is solo-maintained.
- Do not require self-approval or an unavailable second human reviewer.
- Require conversation resolution where supported.
- Dismissal of stale approvals becomes relevant only when an independent reviewer is actually used.

## Required automated gate families

Keep the required-check set small, stable, and unambiguous. Required contexts should represent these gate families:

1. Core CI / tests
2. Backend verification
3. Frontend build/quality
4. Contract verification
5. Secret scanning
6. CodeQL/static security analysis
7. Dependency review / vulnerability audit
8. Tenant-isolation / authorization verification
9. Schema / migration governance
10. Release verification
11. Repository policy / freshness
12. Release-authority / claims control

Do not require every supporting workflow as a branch-protection context. Supporting workflows may remain mandatory inputs to a terminal gate without all becoming separate merge blockers.

Exact required context names must be captured from the current successful GitHub check runs before configuring the ruleset. Do not copy historical context names from predecessor repositories.

## Branch integrity

- Block force pushes.
- Block deletion of `main`.
- Require linear history where practical.
- Restrict direct pushes to `main`.
- Allow administrator bypass only for documented emergency recovery.
- Never use bypass to avoid a failing security, tenant, schema, or release check.

## Public-repository security

Enable, where available:

- secret scanning;
- push protection for supported secrets;
- dependency graph;
- Dependabot security updates;
- private vulnerability reporting;
- CodeQL/code scanning.

## Evidence rule

The live GitHub configuration is authoritative. Repository documentation describes the intended configuration and must not be presented as proof that an administrative setting is enabled until the setting is independently verified.
