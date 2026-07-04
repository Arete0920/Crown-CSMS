# Production certification runtime blocker

Status: HOLD / NO-GO until the workflow is rerun and passes.

PR #1237 production certification was blocked on one governed production runtime value: the primary key of the production school row that should be used for certification.

Required value:

```text
core_school.pk / core_school.id for the production certification school row
```

This value must be supplied as `CROWN_LIVE_SCHOOL_ID` in GitHub Actions variables or secrets before the production certification crawler can honestly pass against `https://crown-api-prod.azurewebsites.net`.

Do not use the sandbox slug `heritage-core` as `X-School-Id`. The backend validates `X-School-Id` as a UUID and then checks that the UUID exists in `core_school`.

Do not use a demo/default UUID unless it is proven to be the production `core_school` primary key used by the deployed runtime.

## Verified production lookup results

A read-only production PostgreSQL query was run against the database settings backing `crown-api-prod`. App Service database settings were read without printing secret values. The `DB_PASSWORD` setting was a Key Vault reference, so the value had to be resolved in memory before connecting.

Initial name-filter query executed:

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

Broader read-only sweep executed:

```sql
SELECT id::text, name
FROM core_school
ORDER BY name;
```

Result:

```text
156b351b-1d06-40cd-b36b-2c08150b69af    GP School
```

Decision classification:

```text
The production database reachable through crown-api-prod contains exactly one core_school row.
Its name is GP School, not Heritage Christian Academy.
The UUID is therefore the only valid production X-School-Id candidate for the currently deployed production database path, but using it means the production certification evidence is for the currently seeded production school row, not a row named Heritage Christian Academy.
```

## Next action

Set the GitHub variable to the only production `core_school` UUID and rerun the failed production certification workflow:

```bash
gh variable set CROWN_LIVE_SCHOOL_ID --repo tcmegahan/Crown2026 --body "156b351b-1d06-40cd-b36b-2c08150b69af"
gh run rerun 28675330141 --repo tcmegahan/Crown2026 --failed
```

If the workflow passes, separately resolve the naming/data-governance mismatch between the product evidence language and the seeded production school name. If the workflow fails, inspect the new failure as the next runtime blocker.

## Safe lookup options retained

1. Query production PostgreSQL directly and return only school UUIDs and names.
2. Run a production Django shell or management command in the running application container and return only school UUIDs and names.
3. Add a temporary read-only ops-protected diagnostic command or endpoint that returns only production school UUIDs and names, then remove it after the GitHub variable is set.
