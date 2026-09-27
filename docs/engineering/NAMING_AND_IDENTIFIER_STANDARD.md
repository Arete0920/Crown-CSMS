# CROWN Naming and Identifier Standard

**Status:** current canonical engineering standard
**Repository:** `Arete0920/Crown-CSMS`

## 1. Product and repository names

- Public/product name: **CROWN**
- Repository name: **Crown-CSMS**
- Repository identity: **Arete0920/Crown-CSMS**
- Daycare product: **Diadem Daycare Solutions**
- Scheduling product: **Kairos**
- Financial-aid product: **Jireh**
- Knowledge base: **Solomon**

Predecessor names may appear only in clearly marked historical/provenance records or bounded compatibility identifiers.

## 2. Python

- modules/packages: `snake_case`
- functions/variables: `snake_case`
- classes/models: `PascalCase`
- constants: `UPPER_SNAKE_CASE`
- Django app labels: stable `snake_case`; do not rename an established app label without migration/runtime analysis
- model choice keys: stable `snake_case`
- human-facing choice labels: current product terminology

## 3. JavaScript / TypeScript / React

- variables/functions: `camelCase`
- React components/types/interfaces: `PascalCase`
- constants: established project convention; prefer descriptive immutable names
- files:
  - React components/pages: `PascalCase.jsx|tsx`
  - utilities/config modules: current local convention, normally `camelCase` or established package pattern
- do not introduce vendor/product names into identifiers

## 4. URLs and API routes

- public web paths: lower-case kebab-case
- API paths: lower-case, resource-oriented, versioned under the canonical API prefix
- compatibility routes must be explicitly documented as legacy aliases
- new functionality must use canonical current product/domain terminology rather than compatibility names

## 5. Database and migrations

- schema identifiers: `snake_case`
- migrations are append-only historical records after establishment
- do not rewrite an applied migration solely for cosmetic renaming
- use a forward migration for current schema/display-name changes
- compatibility keys may remain stable when changing them would break stored data or integrations

## 6. Git branches

Preferred prefixes:

- `feature/`
- `fix/`
- `test/`
- `docs/`
- `chore/`
- `ci/`
- `security/`
- `compliance/`
- `architecture/`
- `maintenance/`
- `release/`
- `hotfix/`

Branch names must describe the work, not the tool used to perform it.

## 7. Commits and pull requests

Commit pattern:

`<type>: <concise outcome>`

Preferred types:

- `feat`
- `fix`
- `test`
- `docs`
- `refactor`
- `chore`
- `ci`
- `security`
- `schema`
- `release`
- `governance`

PR titles should use the same concise outcome-oriented style.

## 8. Documentation

- current authority documents use current CROWN terminology
- historical records must be visibly labeled historical/superseded
- current operational instructions must use the current repository identity
- do not embed developer-specific absolute filesystem paths
- do not commit real credentials or reusable demo passwords
- named competitors and development-assistance vendors are prohibited from current repository content under the applicable hygiene policies

## 9. Compatibility naming

A legacy identifier may remain only when all are true:

1. changing it could break stored data, migrations, integrations, or routes;
2. the current human-facing name is correct;
3. the legacy identifier is documented as compatibility-only;
4. new code does not expand reliance on the old identifier;
5. a retirement condition is recorded when retirement is practical.

## 10. Enforcement

Naming consistency is enforced through:

- repository policy checks;
- competitor/vendor-name hygiene;
- repository identity/naming hygiene;
- code review;
- schema governance;
- canonical-document review.

Exceptions require an explicit compatibility or historical-provenance rationale.
