# Security Policy

CROWN handles school operations data and is designed for environments involving students, families, staff, communications, billing, and school records.

## Reporting a vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Report privately to the repository owner or designated security contact.

## Sensitive data rules

Never commit:
- passwords
- API keys
- tokens
- refresh tokens
- real student data
- real family data
- real staff data
- real financial data
- production .env files
- tenant secrets
- private certificates
- database dumps
- Microsoft 365 client secrets

## Public repository rule

All examples must use placeholders or environment variables. Sandbox credentials must not be committed even if they are non-production.

## Tenant isolation

Any vulnerability that can expose data across schools or tenants is treated as critical until proven otherwise.
