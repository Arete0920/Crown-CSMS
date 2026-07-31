# CROWN Known Limitations and Release Disposition

**Status:** Canonical current limitations register  
**Effective date:** 2026-07-31  
**Repository basis:** `tcmegahan/Crown2026`  
**Controlling program:** GitHub issue `#1619`

This register records current repository, runtime, operational, legal, and buyer-handoff limitations. It does not authorize production, buyer turnover, payment processing, or legal-compliance claims.

## Current disposition

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DISABLED AND REQUIRED TO FAIL CLOSED**
- Immutable release candidate: **NOT YET SELECTED**
- Protected-history remediation: **NOT VERIFIED COMPLETE**

## Blocking limitations

| ID | Limitation | Current status | Required closure evidence |
|---|---|---|---|
| KL-001 | Complete authenticated production-surface certification is not established on one deployed SHA. | OPEN / BLOCKING | Lane 1 evidence under `#1620` |
| KL-002 | Role, RBAC, tenant-isolation, escalation-denial, object-authorization, and audit certification is incomplete. | OPEN / BLOCKING | Lane 2 evidence under `#1626` |
| KL-003 | Application rollback and isolated database restore have not been demonstrated with accepted measured RTO/RPO. | OPEN / BLOCKING | Lane 3 evidence under `#1627` |
| KL-004 | Operational secret retrieval, rotation, failed-rotation recovery, revocation, break-glass, and exposed-key retirement are not verified complete. | OPEN / BLOCKING | Lane 4 evidence under `#1628` |
| KL-005 | Privacy, records, contracts, incident response, jurisdiction-specific obligations, and qualified legal disposition are incomplete. | OPEN / BLOCKING | Lane 5 evidence under `#1629` |
| KL-006 | Exact-SHA CI, reproducible deployment, runtime identity, infrastructure, monitoring, alerting, and drift proof are incomplete. | OPEN / BLOCKING | Lane 6 evidence under `#1630` and `#1761` |
| KL-007 | Canonical documentation, runbooks, evidence navigation, known limitations, and buyer-handoff reconciliation remain incomplete. | OPEN / BLOCKING | Lane 7 evidence under `#1631` |
| KL-008 | Founder/Product Owner final authorization has not occurred. | OPEN / BLOCKING | Lane 8 authorization under `#1632` |
| KL-009 | Backend coverage has not yet met the declared 75% threshold on the current audited source identity. | OPEN / BLOCKING | Exact-SHA coverage evidence and remediation under `#1794` |
| KL-010 | Historical private-key exposure and clean-distribution remediation are not verified complete across retained refs and external copies. | OPEN / BLOCKING | Rotation, revocation, protected-history, and clean-bundle evidence |

## Payment-processing limitation

No payment processor is approved for production. Card, ACH, autopay, processor webhook, refund, settlement, dispute, and external payment-confirmation behavior must remain disabled unless a future owner-authorized implementation is completed and certified.

Provider-neutral billing, accounting, ledger, invoice, balance, payment-record, and payment-plan source material does not establish payment-processor readiness.

## Runtime and operational limitations

Repository checks do not prove:

- deployed frontend or backend identity;
- authenticated persona behavior;
- production tenant isolation;
- successful rollback or database restore;
- monitoring and alert delivery;
- secret rotation or break-glass effectiveness;
- external-service ownership or successor access.

These limitations require current execution evidence from the same immutable release identity.

## Privacy and legal limitations

CROWN is not represented as FERPA certified, COPPA certified, universally compliant, regulator approved, or legally suitable for every customer or jurisdiction. Current product behavior, policies, contracts, subprocessors, retention and deletion procedures, incident-response operations, and qualified legal review must be reconciled before stronger claims are made.

## Buyer-handoff limitations

Repository transfer alone does not transfer or verify:

- cloud subscriptions and billing;
- domains, DNS, certificates, email, Microsoft 365, or Entra registrations;
- GitHub administrator authority, environments, secrets, variables, and approval rules;
- monitoring, backup, recovery, and incident contacts;
- payment, communications, analytics, or support accounts;
- trademarks, contracts, licenses, assignments, or other intellectual-property records.

Operational turnover requires verified successor identities, external-account transfer, credential rotation, clean-clone setup, exact-SHA evidence, accepted residual risk, and explicit owner authorization.

## Historical records

Earlier dated limitation registers, release scorecards, ship-candidate files, and completion boards are historical context only. They do not override this register, issue `#1619`, current exact-SHA evidence, deployed-runtime evidence, or explicit Founder/Product Owner authority.
