# Jireh SGO | Standalone scholarship administrator foundation

**Status: DEVELOPMENT / NO PRODUCTION CERTIFICATION / NO LIVE FUND MOVEMENT**

## Scope implemented in foundation
- SGO organizations, explicit active SGO memberships and viewer/reviewer/admin roles.
- Per-organization programs with year, funding source and rule-version reference.
- Pseudonymous applications with program and organization scoping.
- Human-attested eligibility linked to opaque evidence-reference keys, not automatic legal qualification.
- Positive noncash award commitments, duplicate-award guard and organization-scoped audit events.

## Product contract
SGO programs, policies and decisions are separately governed from school-controlled institutional aid. CROWN school user roles never grant SGO authorization. Staff and superuser flags do not bypass explicit SGO memberships in the domain service. School UUIDs are only opaque references, not proof of authorization to read school PII.

The foundation must never claim an organization is IRS listed based solely on an administrator-entered flag. The service does not create bank transfers, cash payments, refundable balances, tax filings or compliance certificates. SGO fund custody belongs to the grantor's financial provider.

## Before external rollout
1. Approve SGO identity, provisioning and cross-school data-sharing contracts; build protected SGO API endpoints with external identity and authorization tests.
2. Verify 25F/current state requirements with counsel and real SGO design partners.
3. Implement versioned eligibility configuration, federal/state income thresholds, residency and family-size rules, prior recipient/sibling priorities.
4. Add restricted financial-document collection, consent, encryption, retention and evidence verification; no sensitive documents in event metadata.
5. Build a separately reviewed SGO financial journal and evidence-backed reconciliation; distinguish committed award, paid funds and credited tuition.
6. Implement independent reportable expense validation, overpayment/refund controls, donor contribution accounting, appropriate IRS and state exports.
7. Add an accessible standalone React interface, parent portal, secure partner adapters, repeatable synthetic tests, security review and CI acceptance.
8. Certify each SGO integration separately; keep processing disabled until provider agreement and end-to-end runtime evidence.

## Acceptance
Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`,
and `python manage.py test jireh_sgo.tests` under the repository's supported Python environment. A green static test suite alone does not confer regulatory readiness.
