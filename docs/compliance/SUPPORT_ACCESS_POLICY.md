# CROWN Support Access Policy

**Status:** DRAFT PROCEDURE COMPLETE / APPROVAL AND RUNTIME PROOF NOT EVIDENCED  
**Version:** 1.0  
**Prepared:** 2026-10-07  
**Accountable role:** Founder/Product Owner  
**Approval record:** Not recorded  
**Review:** At least annually and after material access-model changes

## Scope and principles

Apply to employee, contractor, administrator, vendor, and emergency access to customer environments, records, exports, backups, and production infrastructure. School-authorized access must be purpose-limited, least-privileged, tenant-scoped, attributable, and auditable. This policy specifies required behavior; it does not claim every control is implemented.

## Standard access procedure

1. Create a restricted support record identifying the authorized requester, tenant, purpose, requested resources, data sensitivity, access level, start/end time, and permitted actions.
2. Verify requester authority and contractual permissions. Obtain documented authorization from the school's authorized representative before access to customer content, unless a recorded contract or emergency basis permits the specific access.
3. Obtain CROWN approval from the accountable owner or delegate. The requester must not approve their own ordinary privileged-access request. If staffing makes independent approval unavailable, record the conflict and obtain school authorization plus a subsequent independent review; do not describe this as separation of duties.
4. Use a named account with MFA and the smallest required privileges. Prefer read-only access and sanitized diagnostics. Prohibit shared accounts, credential exchange, unmanaged exports, and direct database access without explicit approval.
5. Record grant time, approver, privileges, and expiration. Proposed maximum normal elevation is 8 hours; continued access requires renewed authorization. Verify actual expiry/revocation rather than assuming a ticket expiration changes permissions.
6. Log session identity, tenant, timestamp, approvals, privileged actions, data access/exports where supported, and revocation. Logs must exclude secrets and unnecessary record content.
7. Revoke privileges and active sessions at task completion or expiration. Verify revocation, record the outcome, and resolve unauthorized copies under the approved retention/deletion rules.

## Restricted data and diagnostics

Health, counseling, pastoral, discipline, financial-aid, household finance, and identity records require explicit need and enhanced review. School consent to general support is not blanket access to every sensitive domain. Redact attachments and use synthetic examples where possible. Do not copy customer personal information into public repositories, unapproved diagnostic services, or external guidance systems.

## Emergency access

Break-glass access is limited to active security or material availability incidents where normal approval delay creates harm. Record the incident identifier, lawful/contractual basis, actor, tenant/resource scope, start time, and justification. Alert the accountable owner immediately. Use named, time-bounded credentials; log all actions; revoke and verify revocation when stabilized. Complete retrospective owner and privacy review within 1 business day. Inform the school according to the applicable agreement and incident decision record. Emergency access cannot justify routine convenience.

## Workforce lifecycle and reviews

Approve privileges before grant; review them on role change; revoke accounts, tokens, sessions, and provider access immediately upon termination or suspected compromise. Review privileged access monthly and all support entitlements quarterly. Reconcile accounts against the current workforce/vendor roster and examine expired tickets, dormant accounts, emergency access, and sensitive exports. Retain the reviewed population, reviewer, findings, remediation, and closure proof.

## Evidence and exceptions

Store approvals, access-review records, grant/revoke proof, and incident linkage in restricted storage. Proposed evidence retention is at least 12 months, subject to legal holds, contracts, and auditor requirements. Exceptions require accountable-owner approval, scope, reason, compensating controls, expiration, and follow-up; they cannot waive school authorization, applicable law, or release gates.

Operational closure requires policy approval, named-account/MFA proof, tested tenant and role denial, tested expiry and revocation, support-log coverage, completed access review, and a break-glass exercise. Unimplemented enforcement remains an open technical gap.
