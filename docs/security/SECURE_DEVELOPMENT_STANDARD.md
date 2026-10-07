# Secure Development Standard

## Scope

This standard applies to all CROWN source code, infrastructure, workflows, scripts, services, and automated development activity.

## Data handling

- Use synthetic or irreversibly anonymized school data for development, testing, debugging, demonstrations, and automated analysis.
- Never place production student, family, staff, applicant, health, payment, credential, token, signing-key, session, or customer-contract data into development prompts, logs, fixtures, examples, issue bodies, pull requests, or repository files.
- Treat any exposed secret as compromised: revoke or rotate it, review access evidence, and replace it before continuing.

## Code security

- Use parameterized database operations. Do not build SQL by concatenating untrusted values.
- Enforce authentication, authorization, tenant isolation, and household/user scope at the server boundary.
- Return generic authentication errors and avoid logging request bodies or sensitive values.
- Validate untrusted input at trust boundaries.
- Do not introduce dynamic execution or shell invocation with untrusted data.
- Fail closed when authorization, tenant, payment-integrity, or security preconditions cannot be proven.

## Dependency and supply-chain security

- Existing lockfiles are authoritative for reproducible Node installs.
- New direct dependencies require an entry in `docs/security/dependency-admissions.json` before merge.
- Dependency admission must document the official registry, source repository, maintainer/publisher identity, license, business need, review date, and human approver.
- Dependency vulnerability, license, SBOM, secret, and static-analysis gates must remain enabled and blocking where configured.
- Deployable components must be represented in the SBOM.
- Unknown, unlicensed, or prohibited dependency licenses fail closed.

## Infrastructure and release security

- Infrastructure and deployment configuration changes require automated misconfiguration scanning.
- Production container images must pass blocking vulnerability scanning before registry publication.
- Production deployments must use immutable release identity and verify the deployed SHA end to end.
- Do not weaken release gates, branch protection, tenant tests, authorization tests, secret scanning, dependency review, or security analysis to obtain a green build.

## Automated development isolation

- Automated development should operate only within the repository or a disposable, constrained environment.
- Do not expose production credentials, unrestricted home directories, administrator/root privileges, or unnecessary network access.
- Prefer short-lived, least-privilege credentials and auditable tool activity.
- Read-only review or exploration should not receive write permissions.
- Autonomous or bypass-style execution is permitted only in disposable environments with no sensitive credentials or production access.

## Connector and external-tool security

Before enabling a connector or external tool, document its publisher/source, operations, credential scope, accessible data, external endpoints, audit behavior, revocation method, and human owner. Credentials must be limited to the narrowest actions needed.

## Review

Security scanners are deterministic controls, not substitutes for business-context review. Every change affecting authorization, tenant boundaries, billing, payments, student records, deployment, or recovery requires focused review and exact-head validation.
