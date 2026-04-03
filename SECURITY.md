# Security Policy

## Scope

This policy applies to the Crown2026 repository, including source code, workflows, build and release automation, and operational documentation.

Repository lineage note: Crown2026 is the current active platform repository. Crown-Christian is retained as an archived legacy repository.

## Supported Status

- `main`: actively supported
- tagged release candidates: best-effort support based on active release intent
- stale branches and archived artifacts: no guaranteed support

## Reporting a Vulnerability

Do not report vulnerabilities in public issues or pull requests.

Use private reporting channels:

- Security contact: [Arete Advisory Group](https://www.areteadvisorygroup.org)
- Maintainer contact: [John Megahan on LinkedIn](https://www.linkedin.com/in/john-megahan-935784232)

Suggested subject line:

```text
[SECURITY] Crown2026 vulnerability report
```

## What to Include

- affected component or file path
- vulnerability description
- impact and probable blast radius
- minimal reproduction steps
- whether credentials or student data may be affected

Do not include live secrets unless absolutely necessary.

## Handling Expectations

Security reports are handled on a best-effort basis:

- acknowledge receipt
- validate and classify severity
- rotate/revoke exposed secrets if needed
- remediate and verify
- disclose publicly only when appropriate

## Safe Harbor and Out of Scope

Good-faith security research is welcome. The following are out of scope unless explicitly authorized:

- denial-of-service or destructive testing
- social engineering
- physical attacks
- unauthorized access to third-party systems

## Security Controls and Evidence

Crown2026 uses layered security controls including code scanning, dependency auditing, secret scanning, and branch governance checks.

Operational evidence and release security artifacts are maintained under:

- [docs/release/SECURITY_GATES_EVIDENCE.md](docs/release/SECURITY_GATES_EVIDENCE.md)
- [docs/release/BRANCH_PROTECTION_EVIDENCE.md](docs/release/BRANCH_PROTECTION_EVIDENCE.md)
- [docs/release/FINAL_RELEASE_GATE.md](docs/release/FINAL_RELEASE_GATE.md)
