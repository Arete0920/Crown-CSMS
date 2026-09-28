# CROWN Repository Workflow

Use one branch and one pull request for each coherent, reversible outcome.

Before editing, record the base SHA, scope, validation plan, decision owner, and rollback action.

Every non-trivial change must:
- be reviewable line by line;
- include appropriate tests;
- preserve tenant and permission boundaries;
- pass applicable CI, security, dependency, schema, build, and route checks;
- record the exact head being evaluated;
- avoid unsupported release claims.

Authentication, RBAC, tenant isolation, migrations, deployment, dependencies, and security-sensitive configuration require explicit scope and proportional verification.

Production readiness is determined only from the exact repository head and its current release evidence.
