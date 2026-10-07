# Connector Security Standard

Every connector, tool server, automation account, and external integration with access to CROWN resources is part of the trusted software supply chain.

## Required registration

Before production use, record:

- publisher or authoritative source;
- business owner and technical owner;
- exact operations exposed;
- credential type and scope;
- repositories, tenants, environments, and data classes reachable;
- outbound domains/endpoints;
- logging and evidence retained;
- revocation and rotation procedure;
- incident-disable procedure;
- last security review date.

## Minimum controls

1. Use vendor-published or otherwise verified implementations when available.
2. Prefer fine-grained, short-lived credentials over broad personal access tokens.
3. Grant read-only access unless a write action is required.
4. Separate development, test, and production identities.
5. Deny access to production student, family, health, payment, or credential data unless the integration explicitly requires it and has been approved.
6. Restrict network egress to required destinations where practical.
7. Log material actions and permission changes.
8. Review tool descriptions, returned instructions, and endpoint behavior as untrusted input.
9. Provide a rapid revocation path and test it.
10. Re-review after material permission, scope, vendor, or endpoint changes.

## Fail-closed rule

If source provenance, credential scope, reachable data, or auditability cannot be established, the connector is not approved for production use.
