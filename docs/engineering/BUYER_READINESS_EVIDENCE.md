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

## Follow-up inspection on 2026-10-02 (Azure handled separately by owner)

- Main advanced to `b27dc66df5be4cfd18b34e2671f7b6a1c7023585`. PR #60 head `19acb6578208760c3c31761c696c59021d8c1222` completed 27 workflows successfully; Buyer History Evidence failed as designed. Reconcile fresh checks after updates; these results do not certify a later head.
- Retained CodeQL artifacts from run `36977090440` contain zero Python results and one JavaScript result (`js/incomplete-url-substring-sanitization`) in the production certification crawler. The hostname suffix now requires a DNS label boundary, so `evilvisualstudio.com` cannot qualify as an allowed telemetry host.
- Local unfiltered `pip-audit 2.10.1 --strict` runs against backend and load-test requirements both returned no known vulnerabilities. The two historic ignore rules are removed and their dated risk acceptances retired. These are fresh resolutions of requirement constraints, not immutable Python deployment lockfiles.
- Wallet was outside the routine dependency/license inventories. Its first resolved audit reported three high-severity affected packages. The compatible Joi 17.13.8 override removes the Joi finding; `node-forge` 1.4.0 and its parent `passkit-generator` remain high-severity affected entries. Registry metadata lists node-forge 1.4.0 as latest; the advisory affects versions through 1.4.0. Do not claim this component is cleared or deploy it until a patched implementation is audited and signing behavior is verified. No vulnerability suppression is added.
- Wallet now has a committed lockfile, Docker installs with `npm ci`, and dependency/license jobs include it. Node license reports describe locked package versions, integrity and reported license expressions; they remain inventories requiring legal decisions.
- Azure credentials, deployment and hosted checks are assigned to the owner and are outside this continuation. No Sonar service configuration has been established.

## OWASP supplemental scan setup

The manual **OWASP Buyer Dependency Evidence** workflow requires `NVD_API_KEY` as an Actions secret and `DEPENDENCY_CHECK_IMAGE` as an Actions variable containing a reviewed official `owasp/dependency-check@sha256:<digest>` image. It records tool version, image digest and source SHA, scans backend plus both Node lockfiles, retains JSON/HTML, and rejects findings at CVSS 7 or higher. Missing configuration fails explicitly. This workflow has not run against an NVD-backed database and establishes no clearance. Python support is experimental; retain pip-audit and npm audit as complementary checks. See [OWASP documentation](https://dependency-check.github.io/DependencyCheck/) and [NVD API key registration](https://nvd.nist.gov/developers/request-an-api-key).

## Verified follow-up findings

At PR head `274c1acbb1739c50b96759e1678bff4dc3d52592`, retained CodeQL artifacts from run `37018754230` contain zero Python and zero JavaScript results. This closes the observed crawler finding for that scanned source; it does not clear historic secrets or dependencies. Node license inventories report 79 Wallet and 415 frontend locked packages, with no missing reported license labels. Frontend includes MPL-2.0 and CC-BY-4.0; node-forge offers `(BSD-3-Clause OR GPL-2.0)`. Review applicable obligations and document license selection; do not equate labels with legal clearance.

The previous Dependency Review job only printed that review was unavailable and exited successfully. It is replaced with GitHub's pinned review action at a high-severity failure threshold, with no skip-success fallback. Dependency-graph access failures must remain visible. SBOM generation now includes Wallet. The OWASP and Sonar workflows remain unconfigured/unexecuted; Azure remains assigned to the owner. New checks must be read against the updated PR head.

Python license inventory from run `37019218948` contains 76 reported packages; review `psycopg` and `psycopg-binary` (`LGPL-3.0-only`) and `certifi` (`MPL-2.0`). This is an installed-environment inventory, which may include analysis tooling; reconcile it to the delivered runtime. Wallet's container baseline is aligned to Node 24, matching the dependency-audit runtime. Actual image build and signing behavior still require verification.

## Full local backend and isolated history evidence

Measured PR source: `a2b6e080003c20f164300a2ed1f9f09979ee9f45`. The complete backend suite under coverage 7.15.2 returned **4,855 passed, 19 skipped, five warnings and 138 subtests passed** in 1,173.11 seconds. Skips require PostgreSQL locking or PowerShell and are not local passes. Broad backend coverage is **75.230545%** (37,200 / 49,448 statements); the unchanged governed operational-inclusive scope is **79.122769%** (36,800 / 46,510). The existing 75% gate passes; the 80% buyer target is not reached. Subsequent documentation/container changes do not create new measured evidence for their source SHA.

All 39 workflows at that PR source completed: 36 successful, with Dependency Review (disabled Dependency Graph), Buyer History Evidence (known exposure) and Dependency Audit (Wallet node-forge risk) failing. No failure is waived. Configure Dependency Graph at `https://github.com/Arete0920/Crown-CSMS/settings/security_analysis` to enable the actual review action.

An isolated, local history rewrite removed only the known forbidden path across 96 retained refs and 4,707 commits. Comparing original main `b27dc66df5be4cfd18b34e2671f7b6a1c7023585` to mapped main `71b02696b59d8e1435674d6af81e19c0853acb52` confirms every other file blob is unchanged. No rewrite was pushed. Gitleaks 8.30.1, verified against its release checksum, scanned approximately 713 MB of retained history and returned 88 candidates: 79 match existing reviewed candidate hashes; six are explicit documentation placeholders; three token candidates in `docs/DAY2_DASHBOARD_ENDPOINTS.md` remain unresolved. The prior source-locked 24-candidate manifest does not match this preview's full observed candidate set, so its existing push runner cannot be treated as fresh authorization. Do not distribute the preview or push rewritten refs until candidate review, operational key retirement and fresh authorization are complete.

A retained evidence pack includes coverage XML/JSON, governed metrics, JUnit output, complete test logs, source/digest metadata and metadata-only history adjudication. Raw candidate values and source/history bundles are excluded. Tests and code scanning do not establish hosted runtime or license/IP clearance. Azure remains assigned to the owner.
