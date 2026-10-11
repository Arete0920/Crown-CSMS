# Survey Intelligence — Respondent Privacy and Approval Contract

**Status:** Proposed control design; requires school-specific privacy/legal sign-off and technical evidence before use.
**Applies to:** CROWN Survey Intelligence, Kingdom Path and Crown Compass.
**Tracking:** Issue #204 SI-P02. Subordinate to CROWN's current student privacy program, tenant and release canons.

## Purpose and legal-applicability test

Survey administrators must record the intended service purpose, school identity, respondent age group, contract/funding applicability, jurisdiction, applicable notice/inspection/consent/opt-out rules, sensitive topics, access matrix, retention policy, and the school's authorizing decision. No generic checkbox claiming automatic compliance is sufficient. Federal and state obligations vary by school type, funding, audience and survey content. CROWN engineering cannot determine a school's legal obligations merely from a product configuration.

Official starting references for reviewer verification:
- Education records and covered school requirements: https://studentprivacy.ed.gov/content/family-educational-rights-and-privacy-act
- Protected survey topics and covered education-program recipients: https://studentprivacy.ed.gov/faq/what-protection-pupil-rights-amendment-ppra
- School authorization to process child information within educational purposes: https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions
- School privacy notices and local policies: https://studentprivacy.ed.gov/faq/what-policies-must-local-education-agency-lea-develop-under-protection-pupil-rights-amendment

Review sources again at the actual release date. This document is not legal advice or evidence that any specific independent school is subject to all federal requirements.

## Collection-mode contract

| Mode | Respondent information | Collection behavior required | Raw access | Launch readiness |
| --- | --- | --- | --- | --- |
| Anonymous | No intended responder/household/student binding | No respondent authentication linkage, stored identifying metadata or answer-correlated invitation trail. Audit proxy, security/CDN/web-server logs, IP retention and access timestamps for re-identification. Never promise that identity is technically impossible without independent testing. | No respondent identity. Suppressed aggregates by default; restricted free text if added later. | Adult-only pilot candidate after audit |
| Confidential | Respondent may be known to system; data use is limited | Clearly explain who can access responses and whether attribution is retained; isolate respondent keys from ordinary report readers; enforce purpose and retention. | Separately authorized restricted users with audit logging. | Blocked until implemented/tested |
| Identifiable | Identifiers intentionally collected | Explicit informed notice and appropriate consent/authorization; check school ownership of student/family/application keys through canonical services, not caller-provided IDs. | Purpose-specific least privilege with audit and approved export controls. | Blocked until implemented/tested |

### Minimum technical controls, all modes

1. Tenant ID must originate from authenticated/validated CROWN tenant authority. Never trust school IDs in form JSON.
2. Every related identity, school, campaign, application, question, survey publication and report must resolve to the same authorized tenant.
3. Role/action permissions on the server for creation, approval, collection configuration, reporting, drill-down and export. Hiding buttons is not authorization.
4. Record publication approval with an immutable questionnaire and notice version before launch. Reject changes to any already published/answered question without a new governed version.
5. Expiring, unguessable collection tokens; rotation/revocation; no unrestricted open endpoint. Abuse controls backed by an available shared store and tested for failures.
6. Explicit duplicate/refresh/idempotency behavior. A second submission must never mutate an existing anonymous respondent's answers.
7. Input validation: maximum body size, allowed question keys/types, finite scale values, supported choices, duplicates, required answers, one tenant-safe transaction.
8. Validate sensitive-topic flags before publication; child-facing surveys require separate consent/inspection workflows and legal review.
9. Data minimization and no arbitrary browser/device/request metadata in anonymous response records; review infrastructure logs for indirect identifiers.
10. No automatic posting of individual responses, financial/student information or unsuppressed raw text to external guidance systems.
11. Separate authorization and entitlement verification for Kingdom Path, Compass, exports, dashboards and automated reports.
12. Suppress small sample cells and prevent subtraction/complementary disclosure across reports, filters, time periods or exports. Provisional 10-total/5-visible-cell constraints are a minimum test case, not universal anonymity proof.

## Proposed adult anonymous pilot notice — DRAFT, not approved

Survey heading: [School name] — [Survey title]

> The school is requesting voluntary feedback about your experience to identify opportunities for improvement. You may skip any question or leave without submitting. Do not enter your name, your child's name, personal financial details, medical information or other identifying facts. The school intends to review responses only through appropriately restricted, aggregated reports. Because small groups and contextual details can sometimes identify respondents, complete anonymity cannot be guaranteed until the technical and operational safeguards are independently verified. Survey answers will not be used to make individual student decisions. For information about school data practices, contact [school-authorized privacy contact]. The school-approved retention and deletion policy is [approved retention summary].

This text **must not be published as-is**. Remove the promise of aggregated-only use unless it matches actual restricted administration, audit logging, backups, exports, vendor operations and school contracts. School leadership and reviewer must approve final notice and exact technical meaning. Do not put identifiable recipient tokens or responses in analytics links.

## Decision/approval matrix

| Decision | Accountable approval | Required evidence before distribution |
| --- | --- | --- |
| Research purpose, audience, questionnaire | School sponsor | Instrument version, author/provenance and user-comprehension review |
| Adult-only vs child-facing | School administrator + privacy reviewer | Age rule, invitation audience validation; child policy if applicable |
| Protected topics screening | School's qualified legal/privacy reviewer | Funding/jurisdiction analysis, family notice and consent/inspection/opt-out decision |
| Collection mode and truthful language | Privacy reviewer + security owner | Application + infrastructure metadata audit; consent/no-PII tests |
| Report audience and exports | School governance owner + security owner | Permission matrix, small-cell test results, audit events and restricted export policy |
| Retention, deletion and backup lifecycle | School contract owner + privacy/security owner | Written periods, triggers, legal hold, vendor backup treatment and deletion evidence |
| Live distribution | School sponsor + release authority | Exact instrument version, school approval, successful E2E rehearsal and operational acceptance |

## Access matrix — target, not implemented guarantees

| Role | Drafts | Publish | Raw response | Safe aggregate | Export |
| --- | --- | --- | --- | --- | --- |
| School survey administrator (explicit grant) | Yes | Explicit approval only | No, for anonymous mode | Yes after suppression | Scoped/audited only |
| Head of school | Configured grant | Explicit approval only | No, for anonymous mode | Yes after suppression | Configured and audited |
| Admissions or enrollment staff | Scoped assigned purpose | No by default | No | Kingdom Path purpose-authorized and entitled | No by default |
| Board or Compass leadership | No by default | No | No | Restricted institutional aggregates and entitled | Board-approved, suppressed only |
| Parent or respondent | Own collection interface | No | No | No | No |
| Technical support | No by default | No | No | No by default | No |
| Guidance/analytics integrations | No | No | No | Only approved deidentified aggregate after contract review | No |

## Retention and response rights

No universal numeric retention period is approved here. Configure a legally and contractually reviewed schedule **before** collecting data:
- Data owner, purpose, legal basis, respondent notice version, data elements, collection window.
- Raw responses maximum retention, aggregate report retention, backup retention and security log retention independently specified.
- Deletion/archive events, request-routing for access/withdrawal/deletion when appropriate, legal hold exceptions, incident handling and subprocessor deletion terms.
- Where the survey is genuinely anonymous, do **not** promise to locate or delete a particular individual's response after submission. Explain this limitation before collection.
- Document each deletion/retention decision with a school-authorized actor and independent evidence.

## Readiness and verification gate

Privacy copy, mode flags and database attributes are **not** evidence that the system is anonymous or compliant. Every access and data-flow boundary must pass negative tests, direct URL attacks, cross-school object injection, logging inspection, small-cell/report attacks, export restrictions and disaster-recovery checks before school rollout. Until then collection stays disabled.
