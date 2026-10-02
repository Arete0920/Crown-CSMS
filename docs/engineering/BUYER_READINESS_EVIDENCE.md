# Buyer readiness evidence

Assessment date: 2026-10-02. Inspected main: `231f458a048c106082c7457aed21ec38a0d2fe87`.
This is a dated assessment, not a production authorization or a claim that the repository is flawless.
Re-evaluate every finding against the proposed sale/release SHA.

## Stack and existing controls

CROWN is a web application: Python 3.12, Django 5.2/DRF, Celery; React 19/Vite with JavaScript and TypeScript; PostgreSQL in hosted operation. A separate Node service signs Apple Wallet passes.

| Evidence | Existing control | Buyer interpretation |
|---|---|---|
| Static security | CodeQL for Python and JavaScript/TypeScript | Successful execution does not establish absence of findings. Review retained SARIF and the Security alert inventory. |
| Current secrets | Tracked private-key guard and Gitleaks event-delta scan | Current-tree cleanliness does not clear historical exposures. |
| History | Weekly/manual Gitleaks all-retained-ref scan; Buyer History Evidence | Suppressions remain subject to review. The dedicated known-path gate rejects the documented exposure independently of Gitleaks suppressions. |
| Dependencies | pip-audit, npm audit, dependency review | Document every accepted advisory, date, owner and compensating control. Audit every manifest, including the Wallet service. |
| Tests | pytest, Vitest, Playwright | Record test counts, skipped tests, commands, source SHA and real-versus-mocked scope. |
| Coverage | Exact Main Backend Coverage | Governed backend application threshold is 75%; broad coverage is separately reported. This is not evidence of 80% overall coverage. |
| Quality | ESLint and SonarQube manual analysis | Sonar requires service configuration and an approved server-side quality gate. No Sonar grade is established by adding its workflow. |
| Licensing | Python and Node license inventories; SBOM | Inventories are not legal clearance. Review unknown, reciprocal and incompatible terms, notices, distribution model and ownership. |
| Operations | Azure release preflight and hosted certification workflows | Separate from unit tests and build success; prove migrations, broker, worker, beat, tenant isolation, backup/restore and payments before operational claims. |

## Verified evidence at the inspected SHA

- [Current Main Audit Evidence run 36971418312](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971418312): successful. Logs show 88 frontend unit test files / 653 tests passing and 9 contract files / 32 tests passing. These sets can overlap; do not add the counts together.
- [Dependency Audit run 36971418376](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971418376), [Dependency Scan run 36971418379](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971418379), [CodeQL run 36971418381](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971418381), and [secret scan run 36971418357](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971418357): successful execution. This is not an assertion of zero alerts or zero accepted risks.
- Local tracked private-key guard: PASS. A metadata-only check of the documented historical object confirmed it remains accessible and contains a private-key header; no key bytes were printed or exported.

## Blocking findings and required closure proofs

1. **Historical private-key exposure.** Follow [the existing remediation runbook](../security/ed25519-history-remediation-runbook.md). Identify each trust consumer; independently verify key retirement/replacement and downstream trust updates. Remediate distributable refs and history, scan all retained refs, and verify the actual buyer bundle after restoration. Current-tree redaction does not close this finding. The new history workflow intentionally fails while the forbidden path remains reachable. Checkout refs do not prove elimination from GitHub caches, forks, hidden PR refs or third-party clones.
2. **Azure authentication and runtime evidence.** [Manual preflight run 36971835217](https://github.com/Arete0920/Crown-CSMS/actions/runs/36971835217) failed before login: Azure authentication IDs were missing or invalid; job environment showed no configured IDs or credentials. Restore the authorized Azure service principal or federated identity through repository administration, then rerun inventory. This assessment neither enables nor claims a deployment. Capture exact deployed SHA, production migrations, successful broker connection, worker execution and beat-triggered recurring family notices.
3. **Coverage claim.** Produce exact-sale-SHA backend and frontend coverage reports, including file lists and exclusions. If 80% is the buyer acceptance requirement, add meaningful tests until the agreed scope reaches it. Do not raise a threshold without running the suite, narrow the denominator to create a pass, or describe the present 75% threshold as 80% coverage.
4. **Security and dependency findings.** Export active CodeQL, secret-scanning and Dependabot alerts through an authorized administration surface. Connector access used here does not expose those alert/settings APIs. Reconcile all exceptions (including the two advisory IDs currently ignored by pip-audit). Retain scanner database/tool versions and timestamps. OWASP Dependency-Check can supplement existing ecosystem-native audits, but an NVD-backed run and reviewed results are required before claiming it has passed.
5. **License and IP clearance.** Extend inventories to all shipped manifests and assets. Resolve unknown licenses, preserve attribution and notices, establish contributor/IP assignments and reconcile the [public repository licensing decision](../governance/PUBLIC_REPOSITORY_LICENSING_DECISION.md). A copyleft label alone does not determine an obligation; review how that dependency is used and distributed.
6. **Repository governance.** The inspected branch API returned `protected: false`. Review active rulesets and solo-developer controls before treating this as an enforcement conclusion. Verify secret scanning, push protection and required checks in repository administration. Badges are displays of a named workflow, not a substitute for these controls.

## SonarQube configuration

Configure an existing authorized SonarQube project; this change does not create a service account, subscription or project.

- Actions secret: `SONAR_TOKEN` scoped to the analysis project.
- Actions variables: `SONAR_HOST_URL` (HTTPS) and `SONAR_PROJECT_KEY`.
- For SonarQube Cloud also set `SONAR_ORGANIZATION` to the organization key.
- Approve server-side security/reliability/maintainability and new-code quality requirements. Run **SonarQube Buyer Quality Evidence** on the reviewed branch/SHA. Missing configuration fails explicitly; the workflow waits for the server quality gate.
- Review analysis task identity and dashboard results. This initial workflow analyzes runtime sources and does not import coverage; its result cannot establish 80% coverage. Add verified backend XML and frontend LCOV from the same source SHA before making combined coverage claims.

Official references: [GitHub CodeQL configuration](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options), [SonarQube Cloud GitHub setup](https://docs.sonarsource.com/sonarqube-cloud/getting-started/github), [quality gates](https://docs.sonarsource.com/sonarqube-cloud/standards/quality-gates).

## Buyer evidence pack acceptance

Use a reviewed sale/release SHA and retain source identity, workflow URLs, scanner reports, coverage reports, SBOMs, license decisions and hosted operational proofs. Each entry must identify its scope, timestamp, result and unresolved exceptions. A skipped check, missing credential, missing report, accepted finding or advisory failure is disclosed separately from passed checks. Deliver a remediated and independently verified source bundle only after the security blocker closes.
