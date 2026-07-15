# CROWN Secrets Rotation and Break-Glass Runbook

Status: Required production-readiness procedure
Related issues: #1294, #1296, #1270, #1275
Release posture: CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Purpose

Define the controlled process for rotating production secrets, reviewing secret-store audit records, and using emergency break-glass access without placing root, master, recovery, or long-lived credentials in application runtime or CI/CD.

## Roles

- Founder/Product Owner: final production authority and emergency business authorization.
- Security administrator: secret-store policy, identity, audit, and rotation administration.
- Platform operator: deployment and runtime validation; no standing root access.
- Service owner: confirms functional operation after rotation.
- Incident recorder: preserves timestamps, decisions, evidence references, and follow-up actions.

One person may hold multiple roles in the current operating model, but privileged recovery material must remain under dual control whenever technically possible. Every action must still be attributable to a named individual identity.

## Rotation schedule

| Secret category | Maximum routine age | Immediate rotation triggers |
| --- | ---: | --- |
| Database credentials | 90 days | suspected disclosure, unauthorized access, personnel change, failed audit |
| Microsoft 365 / Graph credentials | 90 days | suspected disclosure, tenant change, consent change; replace with certificate or workload identity where possible |
| Payment-provider credentials | Provider requirement or 90 days, whichever is shorter | suspected disclosure, webhook compromise, processor instruction, personnel change |
| JWT or signing keys | Planned rollover schedule with overlap window | suspected signing-key exposure, invalid issuance, cryptographic policy change |
| Webhook secrets | 90 days | integration compromise, endpoint ownership change, unexpected signature failures |
| Application service credentials | 90 days | suspected disclosure, identity change, workload replacement |
| Human privileged credentials | 90 days or stronger identity-provider policy | role change, departure, suspected compromise, break-glass use |

## Standard rotation procedure

1. Open a controlled change record identifying environment, service, owner, reason, planned window, rollback method, and evidence location.
2. Confirm a current backup or recovery point for affected stateful services.
3. Create the replacement secret in the external store. Do not place the value in tickets, GitHub comments, chat, logs, screenshots, or repository files.
4. Grant the minimum required identity access to the new version.
5. For signing keys or integrations that support overlap, activate the new version while the old version remains temporarily valid.
6. Restart or reload only the affected workloads using the approved deployment path.
7. Verify authentication, health, tenant isolation, critical transactions, and audit-log entries.
8. Revoke the old secret after successful validation and the approved overlap window.
9. Confirm that logs and artifacts contain no resolved secret values.
10. Record completion time, validating operator, affected build or deployment identifier, sanitized audit evidence, and any exceptions.
11. Close the change record only after old access is revoked and service health is confirmed.

## Failed rotation and rollback

- Stop further propagation of the new secret.
- Restore the prior valid version only when it is not suspected compromised.
- If the prior secret may be compromised, do not reactivate it; invoke the incident and recovery path under #1270.
- Record the exact failure, affected services, tenant impact, and recovery decision.
- Rotate dependent secrets when compromise scope is uncertain.

## Audit review

After each production rotation, break-glass event, or suspected exposure, review the external secret-store audit log for:

- authenticating identity and role;
- source workload or human principal;
- requested path or secret object;
- authorization decision;
- read, write, delete, policy, token, and administrative operations;
- timestamp and correlation identifier;
- unexpected access before and after the event.

Application runtime and deployment identities must not be able to disable, alter, or delete audit records.

## Break-glass eligibility

Break-glass access is permitted only when normal identity and deployment paths cannot restore a critical service within the approved incident threshold, or when immediate privileged action is necessary to contain an active security incident.

Break-glass is not a shortcut for routine administration, deployment convenience, missing permissions, or incomplete runbooks.

## Break-glass procedure

1. Declare the incident and record the start time, affected environment, service impact, and reason normal access is insufficient.
2. Obtain explicit authorization from the Founder/Product Owner and security administrator. When one person holds both roles, obtain a second named witness whenever available.
3. Retrieve recovery material from the approved offline, dual-control location. Never retrieve it from GitHub, application configuration, CI variables, chat, email, or a developer workstation file.
4. Use a named, MFA-protected emergency identity or the platform recovery process. Do not share credentials.
5. Apply the narrowest time-bounded privilege capable of resolving the incident.
6. Record each privileged action and correlation identifier without recording secret values.
7. Restore normal identity-based operation as soon as possible.
8. Revoke emergency elevation and confirm it cannot be reused.
9. Rotate every credential or key exposed to the emergency session, including recovery material when platform procedures require it.
10. Review audit logs and preserve a sanitized evidence packet.
11. Complete a post-incident review covering cause, actions, impact, recovery time, control failures, and corrective work.

## Root and recovery material policy

- Vault root tokens, unseal or recovery keys, Azure owner credentials, and equivalent master credentials are prohibited from GitHub Actions, repository files, application runtime, container images, ordinary password managers, tickets, and chat.
- Recovery material must be encrypted, offline, access-controlled, and divided under dual control when supported.
- Root access must be disabled or revoked after initial configuration whenever the platform permits.
- Any root or recovery use triggers mandatory audit review and post-event rotation or regeneration.

## Evidence locations

Each completed exercise or production event must record:

- change or incident identifier;
- date and UTC timestamps;
- environment and service;
- identities and approvers;
- reason and scope;
- deployment or build identifier;
- sanitized audit-log reference;
- validation results;
- revocation confirmation;
- follow-up issue numbers.

Evidence must not contain secret values, tokens, private keys, raw production data, or unredacted customer information.

## Required exercises before production approval

1. Non-production routine rotation exercise.
2. Non-production failed-rotation recovery exercise.
3. Break-glass tabletop exercise.
4. Sanitized audit-log capture proving identity, decision, path, and timestamp fields.
5. Review of the recovery decision tree under #1270.

Documentation alone does not satisfy these exercises. Production remains not approved until current operational evidence is recorded and #1294 and #1296 are legitimately closed.
