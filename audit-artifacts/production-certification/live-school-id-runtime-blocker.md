# Production certification runtime blocker

Status: HOLD / NO-GO.

PR #1237 production certification is blocked on one governed production runtime value: the primary key of the production school row that should be used for Heritage Christian Academy certification.

Required value:

```text
core_school.pk / core_school.id for the production certification school row
```

This value must be supplied as `CROWN_LIVE_SCHOOL_ID` in GitHub Actions variables or secrets before the production certification crawler can honestly pass against `https://crown-api-prod.azurewebsites.net`.

Do not use the sandbox slug `heritage-core` as `X-School-Id`. The backend validates `X-School-Id` as a UUID and then checks that the UUID exists in `core_school`.

Do not use a demo/default UUID unless it is proven to be the production `core_school` primary key used by the deployed runtime.

## Verified production lookup result

A read-only production PostgreSQL query was run against the database settings backing `crown-api-prod`. App Service database settings were read without printing secret values. The `DB_PASSWORD` setting was a Key Vault reference, so the value had to be resolved in memory before connecting.

Query executed:

```sql
SELECT id::text, name
FROM core_school
WHERE name ILIKE '%Heritage%'
ORDER BY name;
```

Result:

```text
NO HERITAGE ROW FOUND
```

This means the blocker is no longer just an unknown UUID. The production database reachable through `crown-api-prod` does not currently expose a `core_school` row whose name contains `Heritage`.

## Next read-only lookup

Run a broader name sweep before setting any GitHub variable:

```sql
SELECT id::text, name
FROM core_school
ORDER BY name;
```

Use the returned row only if it clearly identifies the intended production certification school. If there are no rows, or if no row is clearly the intended certification tenant, do not set `CROWN_LIVE_SCHOOL_ID`.

## Safe lookup options

1. Query production PostgreSQL directly and return only school UUIDs and names.
2. Run a production Django shell or management command in the running application container and return only school UUIDs and names.
3. Add a temporary read-only ops-protected diagnostic command or endpoint that returns only production school UUIDs and names, then remove it after the GitHub variable is set.

Example Django lookup:

```python
from core.models import School
for school in School.objects.order_by("name"):
    print(school.pk, school.name)
```

After obtaining the correct UUID:

```bash
gh variable set CROWN_LIVE_SCHOOL_ID --repo tcmegahan/Crown2026 --body "<uuid>"
gh run rerun 28675330141 --repo tcmegahan/Crown2026 --failed
```
