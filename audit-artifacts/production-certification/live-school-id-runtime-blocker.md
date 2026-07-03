# Production certification runtime blocker

Status: HOLD / NO-GO.

PR #1237 production certification is blocked on one governed production runtime value: the primary key of the Heritage Christian Academy row in the production PostgreSQL `core_school` table.

Required value:

```text
core_school.pk where name matches Heritage Christian Academy
```

This value must be supplied as `CROWN_LIVE_SCHOOL_ID` in GitHub Actions variables or secrets before the production certification crawler can honestly pass against `https://crown-api-prod.azurewebsites.net`.

Do not use the sandbox slug `heritage-core` as `X-School-Id`. The backend validates `X-School-Id` as a UUID and then checks that the UUID exists in `core_school`.

Do not use a demo/default UUID unless it is proven to be the production `core_school.pk` for Heritage Christian Academy.

Safe lookup options:

1. Query production PostgreSQL directly and return only the UUID and school name.
2. Run a production Django shell or management command in the running application container and return only the UUID and school name.
3. Add a temporary read-only ops-protected diagnostic command or endpoint that returns only the Heritage school UUID, then remove it after the GitHub variable is set.

Example Django lookup:

```python
from core.models import School
for school in School.objects.filter(name__icontains="Heritage"):
    print(school.pk, school.name)
```

After obtaining the UUID:

```bash
gh variable set CROWN_LIVE_SCHOOL_ID --repo tcmegahan/Crown2026 --body "<uuid>"
gh run rerun 28675330141 --repo tcmegahan/Crown2026 --failed
```
