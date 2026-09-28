# GitHub Repository Administration Baseline

**Repository:** `Arete0920/Crown-CSMS`
**Applies to:** public repository administration settings
**Owner:** repository owner
**Review cadence:** quarterly and after material security/release changes

## Main branch / ruleset

Configure a ruleset or equivalent protection for `main` with:

- pull request required;
- zero required approvals while CROWN is solo-maintained;
- required automated checks representing the approved gate families;
- conversation resolution enabled;
- force pushes blocked;
- branch deletion blocked;
- linear history enabled where compatible with the chosen merge method;
- direct pushes blocked except documented emergency administrator recovery;
- bypass never used to evade failing security, tenant, schema, dependency, or release checks.

## Security features

Enable where the GitHub plan supports them:

- secret scanning;
- push protection;
- dependency graph;
- Dependabot alerts/security updates;
- CodeQL/code scanning;
- private vulnerability reporting.

## Repository presentation

Set and periodically verify:

- concise repository description;
- official product/site URL when appropriate;
- relevant topics only;
- explicit license decision;
- current README orientation;
- no customer credentials, private contracts, student/family data, or investor-confidential material.

## Required-check design

Use a small terminal set of stable required contexts. Supporting workflows should feed those gates instead of every specialized workflow becoming an independent branch-protection requirement.

Target gate families:

- core CI;
- backend;
- frontend;
- contracts;
- security;
- dependencies;
- tenant/authorization;
- schema/migrations;
- repository policy;
- release verification;
- release authority.

## Quarterly repository health review

Review:

1. open PRs and stale branches;
2. required-check set and workflow duplication;
3. dependency/security alerts;
4. permissions and CODEOWNERS;
5. public-data exposure;
6. archived vs current documentation;
7. release tags and immutable mappings;
8. runtime/deployment workflows;
9. compatibility namespaces such as legacy product/app labels;
10. README, security policy, supported versions, and repository metadata.

Record only material findings or changes; do not create evidence churn for unchanged settings.
