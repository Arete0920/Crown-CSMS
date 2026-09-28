# Security Policy

CROWN handles school operations data and is designed for environments involving students, families, staff, communications, billing, and school records.

## Supported security posture

Security fixes are applied to the current supported `main` line and any explicitly identified release candidate under active verification. Historical tags and archived release evidence are not implicitly supported production lines.

## Reporting a vulnerability

Do not open a public GitHub issue for a suspected vulnerability.

Report privately to the repository owner through GitHub's private vulnerability-reporting/security-advisory path when enabled. If private vulnerability reporting is unavailable, contact the repository owner through the private contact channel identified in the repository profile rather than posting exploit details publicly.

Include, when known:

- affected component and exact revision;
- reproduction steps;
- expected versus observed behavior;
- tenant/school isolation impact;
- student, family, staff, financial, or credential exposure;
- whether exploitation requires authentication;
- suggested containment if immediate action is needed.

## Severity boundary

Treat any credible cross-school or cross-tenant data exposure, authentication bypass, authorization bypass, credential disclosure, destructive data-access flaw, payment-integrity defect, or student-record exposure as critical until proven otherwise.

## Sensitive data rules

Never commit:

- passwords;
- API keys;
- tokens or refresh tokens;
- real student, family, staff, or applicant data;
- real financial or payment data;
- production `.env` files;
- tenant secrets;
- private certificates or signing keys;
- database dumps;
- Microsoft 365 client secrets;
- payment-provider credentials or merchant secrets;
- customer contracts or non-public commercial credentials.

## Public-repository data-handling rule

This repository is public. Public visibility increases the importance of strict secret, credential, student-data, customer-data, and environment-data controls.

All examples and fixtures must use synthetic data, placeholders, or environment variables. Sandbox credentials must not be committed even when they are non-production.

Before any file is committed, assume its full history may become permanently retrievable after publication.

## Required repository controls

The intended security baseline includes:

- secret scanning and push protection where available;
- CodeQL/static analysis;
- dependency vulnerability scanning;
- dependency review for pull requests;
- tenant-isolation and authorization tests;
- immutable release-tag verification;
- protected `main` with required automated checks;
- no force pushes or deletion of the protected release branch.

Repository controls supplement, but do not replace, production runtime controls, vendor security review, backup/recovery testing, or legal/privacy obligations.

## Response discipline

For a credible vulnerability:

1. contain exposure before broad remediation;
2. preserve evidence and exact affected revisions;
3. determine tenant/data scope;
4. rotate compromised credentials where applicable;
5. implement the smallest safe correction;
6. run focused and exact-head regression/security checks;
7. document residual risk and release disposition;
8. notify affected parties when required by contract or law.

Do not publish exploit details before containment and remediation are complete.
