# CROWN Incident Response Policy

**Status:** DRAFT PROCEDURE COMPLETE / APPROVAL AND EXERCISE NOT EVIDENCED  
**Version:** 1.0  
**Prepared:** 2026-10-07  
**Accountable role:** Founder/Product Owner  
**Approval record:** Not recorded  
**Review:** At least annually and after material incidents or system changes

## Purpose and scope

Apply to CROWN services, customer records, source repositories, deployments, workforce devices used for service administration, credentials, and service-provider incidents affecting CROWN. Confirm Diadem and every enabled integration in the SOC 2 scope record. This procedure does not establish that production monitoring or response coverage is operational.

## Responsibilities

- Incident commander: Founder/Product Owner or a recorded delegate; owns severity, containment, escalation, and recovery decisions.
- Technical responder: designated Engineering/Operations role; investigates, preserves evidence, isolates systems, and verifies recovery.
- Privacy/notification reviewer: qualified counsel or designated privacy specialist; determines applicable obligations, recipients, and deadlines.
- Customer liaison: designated Implementation/Customer Success role; sends approved factual communications.
- Evidence custodian: designated responder; maintains timeline, access restrictions, and chain of custody.

Named contacts, deputies, secure contact channels, and after-hours coverage must be verified before operational readiness is closed. A solo operator may perform several roles, but must record decisions and obtain independent review for material incidents when available.

## Severity and internal response targets

These are proposed operating targets, not established service levels or statutory notification periods.

| Severity | Examples | Initial response target after detection |
| --- | --- | --- |
| SEV1 | Suspected cross-tenant disclosure, active compromise, privileged credential exposure, destructive activity, or material service-wide outage | Immediate escalation; acknowledge within 1 hour |
| SEV2 | Credible exploit, limited service disruption, suspected unauthorized access without established scope | Acknowledge within 4 hours |
| SEV3 | Lower-impact issue requiring investigation without evidence of active compromise | Triage within 1 business day |

If facts are uncertain, use the higher credible severity. Start a response record on suspicion; do not wait for proof of exfiltration. Any missed response target becomes a tracked control exception.

## Response procedure

1. Open a restricted incident record with UTC detection time, reporter, affected service/environment, deployed SHA where available, severity, commander, and known facts. Keep customer records and credentials out of public issues.
2. Preserve relevant logs, alerts, configuration, access records, release identity, and forensic snapshots where safe. Record collection time, collector, source, hash where appropriate, and transfers.
3. Contain according to risk: revoke sessions, disable implicated access or integrations, isolate hosts, pause affected exports, and rotate exposed credentials. Preserve evidence before destructive actions when feasible; urgent harm prevention takes priority.
4. Determine affected tenants, record categories, vendors, time window, access paths, and whether data was accessed, altered, disclosed, or lost. Record uncertainty explicitly.
5. Notify the privacy reviewer immediately for any suspected personal-data exposure. Evaluate applicable customer contracts and laws using the notification matrix below.
6. Eradicate the cause and verify fixes. Recovery requires known-good source identity, valid credentials, tenant/access checks, data-integrity checks, monitoring, and commander authorization. Do not restore compromised backups without investigation.
7. Issue approved updates and retain delivery evidence. Close only after corrective actions are assigned, recovery is verified, notification obligations are resolved, and the commander signs the closure record.
8. Complete a post-incident review, normally within 5 business days after stabilization; document cause, impact, missed targets, lessons, owners, and dates. Track long-running corrective actions separately.

## Notification decision record

For each potentially affected customer/jurisdiction, record: customer; law or contract; triggering event; when the applicable clock starts; deadline and timezone; recipients; required contents; responsible reviewer; delivery method; delivery evidence; and any permitted delay basis. Do not substitute a universal 72-hour deadline for customer-specific analysis. Identify school, parent, regulator, insurer, law-enforcement, and provider notifications only where applicable. If a deadline is approaching, escalate immediately; review must not silently postpone required notice.

## Evidence, exercises, and closure

Retain incident records, original evidence references, communications, approvals, and corrective-action tracking in restricted storage. Proposed evidence retention is at least 12 months, extended for legal holds, contracts, or an auditor-agreed period; confirm this before adoption.

Conduct an annual tabletop and another after a material architecture change. Include cross-tenant disclosure, credential compromise, and provider outage scenarios. Record participants, actual response times, notification decisions, recovery checks, failures, and retest outcomes.

Operational closure requires approved policy, verified contacts/coverage, accessible runbooks and evidence storage, tested alert routing, a completed tabletop, and resolved or formally accepted exceptions. A written procedure alone does not close incident-response readiness.
