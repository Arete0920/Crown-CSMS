# CROWN SOC 2 Risk Assessment — Draft for Management Approval

**Status:** DRAFT / NOT APPROVED  
**Prepared:** 2026-10-08  
**Method:** Likelihood 1–5 x Impact 1–5 as defined in `SECURITY_OPERATING_POLICY.md`  
**Boundary:** Scores are a source-evidence-based readiness assessment, not an assertion of incidents or exploitation. Management must approve or revise scores, treatment owners, dates, and residual-risk decisions.

## Scoring

- 1–4 Low
- 5–9 Moderate
- 10–16 High
- 17–25 Critical

## Risk register

| ID | Risk | Evidence basis | Inherent L | Inherent I | Score | Treatment | Residual target | Status |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| R01 | Cross-tenant or unauthorized mutation of customer records | Strong tenant/RBAC source controls now exist, but deployed negative proof and support-access operation remain incomplete | 3 | 5 | 15 High | Maintain explicit tenant/action permissions; execute deployed negative tests, access reviews, support grant/revoke and break-glass exercise | <=8 Moderate | OPEN |
| R02 | Data loss or unacceptable recovery time | Recovery policies and isolated restore mechanics exist; current operational backup identity and measured production-linked restore are not evidenced | 3 | 5 | 15 High | Verify backup inventory/alerts; perform isolated restore from current operational backup; measure RTO/RPO; reconcile critical data | <=6 Moderate | OPEN |
| R03 | Incident notification or containment delay | Incident policy is complete in draft; live contacts, alert routing and participant tabletop are not evidenced | 3 | 5 | 15 High | Approve policy; verify contacts/coverage; test alert-to-response path; run tabletop and resolve findings | <=6 Moderate | OPEN |
| R04 | Unknown or uncontrolled vendor/subprocessor exposure | Candidate register exists; active vendors, regions and executed agreements are not reconciled | 3 | 4 | 12 High | Reconcile active vendors and data flows; complete security reviews, DPAs, incident/retention terms and annual review schedule | <=6 Moderate | OPEN |
| R05 | Misleading readiness/compliance/release claims | Repository now contains explicit claim boundaries, but investor/customer pressure creates recurring risk | 2 | 5 | 10 High | Require evidence-state labels, owner review, and independent assurance before SOC 2 report claims | <=4 Low | OPEN |
| R06 | Key-person dependency / unavailable independent approval | Current operating model relies heavily on the owner/solo maintainer; deputies and continuity access are not evidenced | 4 | 4 | 16 High | Assign deputies, document emergency access and succession/continuity procedures, obtain independent review for material decisions | <=8 Moderate | OPEN |
| R07 | Retention/consent/deletion mismatch with customer or legal obligations | Policies and privacy documents exist; approved schedules, executed terms and lifecycle exercises remain incomplete | 3 | 4 | 12 High | Approve applicability and retention matrix; test access/export/deletion/restore behavior; reconcile contracts and jurisdictions | <=6 Moderate | OPEN |
| R08 | Credential/key or release compromise | Strong source controls exist; current runner outage limits fresh CI, production key/secret operation needs evidence, and Ed25519 history issue #104 remains open | 3 | 5 | 15 High | Close #104, verify production secret/key custody and rotation, restore fresh exact-head CI evidence, verify deployed identity | <=6 Moderate | OPEN |

## Treatment requirements

For every High/Critical risk, management should record:

1. accountable owner and deputy;
2. target completion date;
3. specific evidence required for closure;
4. compensating controls while open;
5. residual likelihood and impact after treatment;
6. explicit acceptance authority and expiry if residual risk is accepted.

No risk acceptance may waive law, customer commitments, tenant isolation, security gates, or required external assurance.

## Approval block

This document remains **DRAFT** until management records:

- approver identity and role;
- approval date;
- confirmed or revised scores;
- treatment owners and due dates;
- residual-risk dispositions;
- next review date.

Until then, the scores above are planning values for readiness prioritization only.
