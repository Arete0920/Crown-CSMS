# Security Policy

## Scope

This policy applies to the Crown2026 repository, its code, workflows, documentation, build surfaces, deployment-related automation, and associated operational artifacts.

Repository lineage note: Crown2026 is the current active platform repository. Crown-Christian is retained as an archived legacy repository.

## Supported status

Security fixes are applied according to current operational priorities.

Because this repository is under active development, support status should be interpreted as follows:

- `main` - active hardening and active development
- tagged releases and release candidates - support depends on current release intent
- stale branches or archived artifacts - no support commitment unless explicitly stated

## Reporting a vulnerability

Do not disclose vulnerabilities publicly.

Do not:

- open a public GitHub issue
- open a public pull request containing exploit details
- post secrets, tokens, stack traces with sensitive values, or operational screenshots in public threads

Instead, report privately to:

- Security contact form: [Arete Advisory Group](https://www.areteadvisorygroup.org)
- Maintainer contact: [John Megahan on LinkedIn](https://www.linkedin.com/in/john-megahan-935784232)

Subject line recommendation:

```text
[SECURITY] Crown2026 vulnerability report
```

## What to include in a report

Please include:

- affected component or file path
- vulnerability description
- impact assessment
- reproduction steps
- proof of concept, if safe to share
- whether secrets, customer data, or deployment surfaces may be affected
- any suggested remediation

## Sensitive content handling

Do not include live credentials in the report body unless absolutely necessary.

Prefer:

- redacted examples
- minimal proof
- rotated or invalidated sample tokens where possible

If you believe a live secret has been exposed:

- mark the report as urgent
- identify the likely secret type
- identify the affected environment if known
- do not repost the secret in multiple locations

## Response expectations

Target handling process:

- acknowledge receipt
- validate the finding
- assess severity and blast radius
- rotate or revoke exposed secrets if applicable
- remediate
- document the fix internally
- disclose publicly only if and when appropriate

Response timing is best-effort and depends on severity and active operational workload.

## Safe harbor

Good-faith security research intended to improve the security of this repository will be treated respectfully.

However, the following are out of scope unless explicitly authorized:

- denial-of-service activity
- destructive testing
- social engineering
- physical attacks
- access to third-party accounts or infrastructure without permission
- retention, reuse, or disclosure of non-public data

## Secret handling expectations

All contributors must:

- avoid committing secrets
- use approved secret storage mechanisms
- rotate any accidentally exposed secrets immediately
- report suspected exposure through the private security channel
- avoid broad permanent allowlisting of sensitive findings without justification

## Dependency and supply-chain expectations

Changes affecting dependencies, CI, build logic, release automation, or deployment workflows may require elevated scrutiny.

Contributors should expect:

- dependency review
- static analysis
- secret scanning
- targeted follow-up proof for release-affecting changes

## Disclosure policy

Public disclosure, if any, is controlled by the repository owner or designated maintainer.

Do not publish details until:

- the issue is validated
- remediation or mitigation is in place
- disclosure timing is approved

## Contact

Primary security contact:

- [Arete Advisory Group](https://www.areteadvisorygroup.org)

Secondary contact:

- [John Megahan on LinkedIn](https://www.linkedin.com/in/john-megahan-935784232)
## Supported Versions

| Version | Supported |
|---|---|
| v0.9.x (pre-launch) | Yes |
| < v0.9.0 | No |

## Reporting a Vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Report security issues privately to `security@crownschoolsystem.com`.

Response targets:

- Acknowledgment within 48 hours
- Status update within 7 days

## Active Security Controls

| Control | Status | Details |
|---|---|---|
| CodeQL static analysis | Active - blocking target | Runs on PRs to `main` and `develop` |
| Dependency audit | Active - blocking target | pip-audit and npm audit |
| Secret scanning | Active - blocking | gitleaks on repository content |
| Branch protection | Enforced target | PR required, approval required, required checks |
| Tenant isolation | Active | Header-based school scoping and tenant guards |
| FERPA audit logging | Active | Audit middleware and structured audit logging |
| JWT authentication | Active | Bearer-token protected API surface |

## Credential Policy

- No credentials, API keys, tokens, or secrets should be committed to this repository.
- Secrets are managed via GitHub Secrets for CI and Azure-managed secret storage in production.
- Any accidental credential exposure is treated as a P0 incident and requires immediate rotation.

## Data Protection

Crown handles student data subject to FERPA and COPPA. See [docs/COMPLIANCE.md](docs/COMPLIANCE.md).

## Security Evidence and Governance Artifacts

Investor and release-governance security evidence is tracked in:

- [docs/release/SECURITY_GATES_EVIDENCE.md](docs/release/SECURITY_GATES_EVIDENCE.md)
- [docs/release/BRANCH_PROTECTION_EVIDENCE.md](docs/release/BRANCH_PROTECTION_EVIDENCE.md)
- [docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md](docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md)
- [docs/release/FINAL_RELEASE_GATE.md](docs/release/FINAL_RELEASE_GATE.md)

## Security Disclosure History

| Date | Finding | Action |
|---|---|---|
| Feb 2026 | Secrets were committed to repository history | History purged and credentials rotated |
| Feb 2026 | Production logs and archives were tracked | Removed from history and ignore rules tightened |
| Mar 2026 | CodeQL was advisory | Blocking behavior restored |
| Mar 2026 | Dependency review was unreliable | Replaced with deterministic audit workflow |
