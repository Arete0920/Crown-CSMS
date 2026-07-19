# CROWN Student-Data Privacy and Compliance Position

**Status:** DOCUMENTED POSITION / NOT LEGAL CERTIFICATION  
**Date:** 2026-07-19  
**Authority:** Founder/Product Owner, subject to legal, security, customer, and jurisdiction-specific review

## 1. Purpose

CROWN is a school-directed management platform that may process education records and other sensitive information about students, families, staff, and school operations. This document defines the intended compliance posture, required controls, evidence gates, and permitted claims.

This document is not legal advice, a regulator-issued certification, a customer-specific determination, or production authorization.

## 2. Approved external language

Use:

> CROWN is designed to support schools in meeting applicable student-data privacy and security obligations through tenant isolation, role-based access, auditability, data-governance controls, contractual restrictions, and evidence-based operations.

Do not use:

- "FERPA certified";
- "COPPA certified";
- "fully compliant with every student privacy law";
- "compliance guaranteed";
- "approved by the U.S. Department of Education";
- any statement that repository documentation alone proves operational or legal compliance.

## 3. FERPA position

FERPA applies directly to educational agencies and institutions receiving applicable U.S. Department of Education funds. CROWN's intended role is a school-directed contractor or service provider processing education records only for the institutional services and legitimate educational interests defined by the school and contract.

For a school to rely on the FERPA school-official exception where applicable, the operating and contractual model must support all of the following:

1. CROWN performs an institutional service or function for which the school would otherwise use employees.
2. The school retains direct control over the use and maintenance of education records.
3. Personally identifiable information is used only for the purpose for which it was disclosed and is not improperly redisclosed.
4. Access is limited to legitimate educational interests and authorized roles.
5. The school's annual FERPA notice and local policy support the applicable school-official criteria.

Required CROWN controls include:

- school/tenant isolation;
- least-privilege role and permission enforcement;
- authenticated access to protected records;
- logging of privileged access, disclosure, export, override, and support access;
- customer-directed retention, correction, export, and deletion procedures;
- restrictions against sale, advertising use, unrelated profiling, or unauthorized redisclosure;
- written customer terms, including a DPA or equivalent data-protection terms;
- subprocessor control and disclosure;
- incident response and customer notification procedures;
- backup, restore, and recovery evidence;
- verified support-access and break-glass controls.

## 4. COPPA position

COPPA may apply to CROWN as an operator when an online service collects personal information from children under 13. School authorization may be relied upon only within the school context, for the use and benefit of the school, and for no unrelated commercial purpose.

Required CROWN controls include:

- clear notice to the school of collection, use, and disclosure practices;
- collection limited to school-authorized educational and operational purposes;
- no behavioral advertising to children or students;
- no sale of children's or student data;
- no unrelated commercial profiling;
- school and parent review/deletion mechanisms where required;
- age-appropriate and role-appropriate account controls;
- reasonable security, confidentiality, and integrity safeguards;
- retention only as long as necessary for the authorized purpose or governing contract;
- an explicit consent and notice model for any direct under-13 experience.

A school consent model must not be used to authorize CROWN's own unrelated commercial use of children's personal information.

## 5. PPRA position

PPRA obligations are primarily school or LEA obligations, but CROWN must support compliant school administration where features involve surveys, analyses, evaluations, protected topics, marketing-related data collection, or parent notice and opt-out workflows.

CROWN must not represent a survey or consent feature as PPRA-compliant merely because a form exists. Required evidence includes configurable notice, inspection, consent or opt-out behavior, protected-topic classification, authorization, and audit history.

## 6. CIPA position

CIPA is an E-Rate-related obligation of eligible schools and libraries concerning internet safety policies and technology protection measures. CROWN is not currently represented as an internet filtering or CIPA certification service.

CROWN may support administrative records, policy acknowledgements, incident records, or evidence workflows, but the school remains responsible for its internet safety policy, filtering solution, public notice or hearing requirements, and E-Rate certifications.

## 7. Additional obligations

Production readiness also requires review of:

- applicable state student-data privacy laws and contractual requirements;
- breach-notification laws;
- health, counseling, discipline, spiritual-life, financial-aid, and other sensitive-data restrictions;
- accessibility obligations and customer requirements;
- record-retention, litigation-hold, and public-record obligations where applicable;
- contractual subprocessor, data-location, deletion, and incident-notification terms.

No single national statement can replace state-by-state and customer-specific review.

## 8. Certification model

CROWN compliance status must be stated by evidence level:

| Level | Meaning | Current claim permitted |
|---|---|---|
| Policy documented | Required policy and control expectations are written | Yes, where the relevant document exists |
| Source control implemented | Repository evidence shows the control exists in code or configuration | Only with exact source evidence |
| Runtime verified | The control is proven against an identified deployed version | Only after current runtime evidence |
| Operationally exercised | Rotation, support access, incident, backup, restore, and recovery exercises are completed | Only after timestamped exercise evidence |
| Contractually ready | DPA, privacy terms, subprocessor terms, and customer responsibilities are approved | Only after legal and commercial approval |
| Legally reviewed | Qualified counsel has reviewed the applicable posture and claims | Not yet claimed |
| Production authorized | All required release gates and Founder/Product Owner approval are complete | Not approved |

## 9. Required evidence before production authorization

- current data inventory and classification;
- data-flow and subprocessor register;
- approved privacy policy and customer-facing notice set;
- approved DPA and contract terms;
- FERPA school-official and legitimate-interest contract support;
- COPPA applicability and consent-path determination;
- PPRA feature and notice/consent assessment;
- state-law applicability matrix for intended customer jurisdictions;
- tenant-isolation and cross-school denial proof;
- authenticated role, permission, and support-access proof;
- audit-log completeness and retention proof;
- export, correction, deletion, and retention procedures;
- incident-response tabletop or controlled exercise;
- backup, restore, rollback, and measured RTO/RPO evidence;
- external secret-store, rotation, audit, and break-glass evidence;
- legal review and Founder/Product Owner acceptance.

## 10. Current decision

CROWN has documented compliance intentions and material technical controls. It is not currently represented as legally certified, universally compliant, or production authorized.

The current approved description is:

> CROWN has a documented student-data privacy posture and is undergoing final technical, operational, contractual, and legal readiness validation.

## 11. Primary official references

- U.S. Department of Education Student Privacy Policy Office, FERPA and vendor guidance: https://studentprivacy.ed.gov/
- FERPA regulations, 34 CFR Part 99: https://studentprivacy.ed.gov/resources/family-educational-rights-and-privacy-act-regulations-ferpa
- Responsibilities of Third-Party Service Providers under FERPA: https://studentprivacy.ed.gov/resources/responsibilities-third-party-service-providers-under-ferpa
- FTC COPPA FAQs: https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions
- U.S. Department of Education PPRA guidance: https://studentprivacy.ed.gov/topic/protection-pupil-rights-amendment-ppra
- USAC E-Rate and CIPA resources: https://www.usac.org/e-rate/
