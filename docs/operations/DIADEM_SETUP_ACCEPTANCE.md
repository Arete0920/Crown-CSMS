# Diadem director configuration — inactive setup workflow

Base: protected main `ec6aaffb7dbef031dcaf92d8a9018dd45bebb7ca`.
Owner: Arete Advisory Group under the master engineering directive.

## Outcome and boundary

An explicitly assigned director with `diadem.daycare.configure` and an active
Daycare entitlement can create and read back inactive centers and rooms at
`/diadem/daycare/setup`. Staff, guardians and legacy school roles do not inherit
configuration authority. Role/permission and tenant state are checked on the
server; browser role values never grant authority.

This is a complete create-and-readback workflow for setup proposals. It is not
center activation, verified policy approval, independent staff credentialing,
child enrollment, admission, reentry, emergency release or full Daycare product
acceptance. Existing custody routes and history are preserved. No external
payments or real customer provisioning are included.

The existing `DaycareSite` and `DaycareRoom` remain canonical. New records are
always inactive. Client-supplied activation, reviewer, tenant and verification
fields are rejected. Identical tenant-local code/payload retries return the same
record; conflicting code reuse returns HTTP 409. Creation and its attributed
audit snapshot commit together or both roll back. Configuration uses the same
entitlement-before-staff lock order as custody operations.

Site mode is explicitly standalone or CROWN-integrated; neither requires a
K-12 Student. New setup currently accepts Delaware (`US-DE`). Historical mode
and jurisdiction default to blank/unknown, never an inferred classification.
New room age/date fields are explicitly **proposed**, nullable and unverified.
They do not supersede the existing custody policy or certify legal compliance.
The setup API cannot activate a room or write policy-verification fields.

## Delaware source and review responsibility

Owner selected Delaware and proposed the daycare director as policy and staff
qualification reviewer on November 2, 2026; credentials remain to be verified.

- [14 DE Admin. Code 933](https://regulations.delaware.gov/AdminCode/title14/933)
- [OCCL regulations and exemptions](https://education.delaware.gov/families/birth-age-5/occl/regulations_and_exemptions/)

Retrieved text and original embedded tables were inspected. Sections 24 and 28
require qualification/eligibility records and external OCCL/CHU determinations.
Section 27 includes age-specific ratios, maximum group sizes, mixed-age and
supervision conditions. A director role or single configured ratio is not proof
of Delaware compliance. Before any activation workflow, verify the actual
facility's license/category/conditions, applicable current policy and effective
dates, director credentials and staff qualifications, and qualified review.
No exception or reduced-staffing rule is activated by this change.

## Required acceptance

- Actual UI -> canonical authenticated API -> director/grant and entitlement
  checks -> atomic service/model/audit -> independently scoped GET readback.
- Two synthetic tenants; denied anonymous, expired token, wrong/revoked role or
  grant, inactive school/organization, absent entitlement, conflicting/foreign
  school headers and foreign site selectors; no disclosure or partial creation.
- Strict payload and invalid ages/dates/capacity rejection; identical retry and
  conflict; simulated audit failure rolls back creation.
- Real PostgreSQL concurrent same-code creation produces one configuration and
  one audit event. The safety lane requires this case to execute, not skip.
- Additive migration preserves existing custody identities/history and leaves
  historical mode/jurisdiction unknown. Pre-0012 restoration uses historical
  models so newer setup fields cannot invalidate the old-schema proof.
- Browser center/room creation, actual readback, source/as-of display, denial,
  stale tenant/session suppression and accessible mobile controls.
- All applicable final-head tests, build, security and repository-policy gates;
  terminal governed disposition under the documented solo-maintainer control.

## Rollback and remaining acceptance

Revert the bounded source change while retaining setup/audit data. New schema
fields are additive and nullable/default-blank; no old rows are reclassified.
Do not delete custody, history or proposed policy evidence during rollback.
Hosted parity/rollout and operational licensing acceptance remain separate.
Source CI, synthetic data and self-review are not independent approval.
