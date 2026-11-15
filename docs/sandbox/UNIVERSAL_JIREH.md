# Isolated local presenter Jireh

This is local source readiness, not hosted activation or live financial authority.
Prepare the dedicated presenter database and normal accounts described in
UNIVERSAL_PRESENTER.md. A fresh isolated database also needs the existing normal
permission catalog (`python manage.py seed_permissions`). This is standard local
application bootstrap, not a new permission policy. The Jireh command checks for
existing AID_DIRECTOR view/edit grants and never creates global grants itself.

```sh
python manage.py prepare_universal_jireh
python manage.py prepare_universal_jireh --apply
```

Read-only preflight refuses missing scope or existing operational Jireh state.
Explicit apply reuses the existing fictional Aid policy/budget seed and verified
Reed family, adds a school-scoped existing Aid Director role to the fictional
finance principal, and creates two independent fictional external SGO programs.
Only that parent receives applicant grants; only that finance principal receives
processor assignments. No SGO organization membership or award/funds authority
is granted. No real partner, school or customer data is copied.

Normal parent login reaches the existing Financial Aid form through the dedicated
`/api/v1/presenter/jireh/aid/family/` realm. Transactions reuse the hosted fixed
fictional-scenario intake service, with separate strict local presenter runtime,
provenance, role, tenant, family and learner checks. Historical Heritage and
hosted buyer runtime/invitation gates remain unchanged. Administrative review and
the Aid wizard use existing ordinary permissions and produce offered awards.
Ordinary approval records a noncash institutional credit and budget allocation;
repeat approval does not duplicate either. Existing family status reads the
result independently. No payment provider or funds transfer is involved.

The existing SGO intake page uses `/api/v1/presenter/jireh/sgo/` for the reserved
presenter only. Submission, optimistic revisions, retry keys, processor queues,
correction requests and family corrections reuse the existing SGO services and
audits. Explicit program grants remain required, in addition to presenter role
and school checks. Other-school program grants and foreign tenant headers deny
access. Parent and processor authority remain distinct.

The command does not overwrite applications, rotate passwords or reset awards.
Destructive bootstrap reset refuses populated Jireh/audit state; whole-scenario
repeat requires a separately verified retained-history lifecycle. Exact-head
browser reload, PostgreSQL locking and hosted acceptance remain additional
release gates beyond local API persistence tests.

Azure activation is NO-GO for this local realm. It intentionally rejects hosted
identities, PostgreSQL and nonlocal configuration. The owner must separately
approve a reviewed hosted presenter implementation and exact revision. Do not
change local flags, substitute a prospect invitation or bypass tenant guards to
activate this command in Azure. No live database, schema, payment or cloud change
is performed by this source increment.
