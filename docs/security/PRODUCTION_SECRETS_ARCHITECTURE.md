# CROWN Production Secrets Architecture

Status: Required production-readiness control
Related issues: #1294, #1296, #1270, #1275
Release posture: CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Control objective

Production secrets must be obtained through identity-based access to an external secret store. Production credentials, tenant secrets, database URLs, signing keys, payment-provider credentials, Microsoft 365 credentials, webhook secrets, private certificates, database dumps, and production `.env` files must not be committed, baked into images, or copied to application disk as unmanaged plaintext.

## Approved target

Preferred implementation: HashiCorp Vault KV v2 with workload or managed identity authentication.

Approved Azure-native alternative: Azure Key Vault with managed identity or workload identity federation.

Long-lived root, master, owner, or recovery credentials are prohibited from application runtime and GitHub Actions.

## Secret domains

The logical secret hierarchy is:

- `secret/crown/global/`
- `secret/crown/environments/sandbox/core-sis`
- `secret/crown/environments/staging/core-sis`
- `secret/crown/environments/production/core-sis`
- `secret/crown/environments/production/billing`
- `secret/crown/environments/production/microsoft365`
- `secret/crown/environments/production/portal-secrets`
- `secret/crown/environments/production/tenants/{tenant_id}`

Azure Key Vault implementations must preserve equivalent separation through vault boundaries, RBAC scopes, tags, naming conventions, and separate identities.

## Identity and authorization model

### Application runtime

- Authenticate through workload identity, managed identity, or another short-lived machine identity.
- Receive read-only access to the minimum environment and service paths required by that workload.
- Deny list, write, delete, metadata mutation, policy administration, identity administration, token creation, and audit configuration.
- Do not expose tenant-specific secrets to workloads that do not serve that tenant boundary.
- Load secrets into process memory only when required; do not write resolved values to logs, artifacts, crash reports, or local files.

### GitHub deployment workflows

- Use OpenID Connect workload identity federation or an equivalent short-lived identity exchange.
- Do not store Vault root tokens, Azure owner credentials, long-lived client secrets, or recovery keys in GitHub repository or environment secrets.
- Limit deployment identity access to the exact deployment environment and operation.
- Separate production deployment identity from application runtime identity.
- Record identity, repository, workflow, environment, requested path, decision, and timestamp in the external audit log.

### Human administration

- Use named individual identities with MFA.
- Prohibit shared administrator accounts.
- Require time-bounded elevation for privileged changes.
- Store recovery material offline under dual control.
- Review privileged access at least quarterly and after personnel or vendor changes.

## Required policy templates

Reference templates are stored under `infra/vault/policies/`:

- `crown-runtime-readonly.hcl`
- `crown-github-deploy-readonly.hcl`

These are templates only. They contain no credentials and do not prove external Vault configuration.

## Audit requirements

The external secret store must log:

- authentication successes and failures;
- identity and role used;
- requested secret path or object;
- read, write, delete, policy, and administrative operations;
- authorization decision;
- source workload or principal;
- timestamp and correlation identifier.

Audit records must be protected from alteration by application and deployment identities, retained according to the approved security and legal retention schedule, and reviewed after break-glass use or suspected exposure.

## Repository controls

Current repository controls include:

- required Gitleaks scanning for pull requests and `main`;
- redacted SARIF evidence artifact generation;
- `.gitignore` exclusions for local env files, private keys, certificates, keystores, local databases, logs, and secret-bearing exports;
- example environment files limited to placeholders.

Repository controls reduce source-control exposure risk. They do not prove external production secret-store configuration, runtime identity, audit retention, rotation execution, or break-glass readiness.

## Production acceptance evidence

Production authorization requires current evidence for all of the following:

1. Secret scan passes on the approved release SHA.
2. No production `.env`, key material, certificate, database dump, or real credential is committed or packaged in the image.
3. External Vault or Azure Key Vault configuration is identified by environment.
4. Runtime identity has read-only least-privilege access.
5. Deployment identity uses short-lived federation and is separate from runtime identity.
6. Audit logging is enabled and a sanitized access-log sample is retained as evidence.
7. Rotation and break-glass procedures have named owners and recorded exercises.
8. Production release authority explicitly confirms closure of #1294 and #1296.

Until all external and operational evidence is recorded, production remains not approved.
