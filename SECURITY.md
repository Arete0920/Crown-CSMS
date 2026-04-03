# Security Policy

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