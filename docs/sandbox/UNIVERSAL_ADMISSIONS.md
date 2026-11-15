# Fictional presenter enrollment conversion

After normal local presenter and existing permission catalog bootstrap:

```sh
python manage.py prepare_universal_admissions
python manage.py prepare_universal_admissions --apply
```

Preflight reads only. Apply reuses the existing Heritage enrollment-conversion
fixture implementation with an explicit owned school and registrar; it does not
invoke the original Heritage reset or grant global permissions. It creates
independent Mercer family, canonical/compatibility learner links, canonical
accepted application and legacy provenance, with an explicitly fictional
countersigned contract and WAIVED deposit as initial dataset facts. No signature
or payment is actually processed, and those initial facts are not evidence of
exercising the signature workflow.

The normal registrar login can perform the existing real enrollment conversion:
strict canonical identity, contract/deposit and authoritative school-year
CoreEnrollment gates remain in force. The endpoint persists the legacy application ENROLLED state
and the canonical enrollment-confirmed audit event. Retry is idempotent. Parent
and foreign tenant context deny the transaction. Independent summary reads verify
the downstream enrolled count. Current CoreStudent lifecycle status remains
APPLICANT; this legacy action does not implement that separate activation
transition, so full active-student onboarding is not claimed.

This completes source acceptance for accepted-applicant conversion. Initial
inquiry, parent application submission, signatures and full enrollment lifecycle
browser acceptance remain separate gaps; do not claim those from seeded contract
facts. Original Heritage seeding/reset defaults remain unchanged. Existing
presenter admissions state is never overwritten; bootstrap destructive reset
correctly refuses protected application history. Retention-aware whole-school
replay is still a remaining gate.

The separately owner-approved DEV activation command includes this fixture in its
single transaction and checks the existing registrar permission catalog. No
Azure, live database, migration, payment or credential change was performed in
this assignment. Follow UNIVERSAL_AZURE_ACTIVATION.md only after separate owner
authorization and exact-revision acceptance. Source revert does not delete
application history or revoke existing normal credentials.
