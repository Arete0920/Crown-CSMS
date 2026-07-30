# CROWN

Christian School Management Solution

> **Repository remediation notice — July 29, 2026**
>
> CROWN is not production-authorized. Buyer operational turnover is not approved, and external payment processing remains disabled and must fail closed. GitHub issue #1619 and its eight open lane issues are the sole controlling production-readiness and buyer-handoff framework. `docs/CURRENT_RELEASE_STATUS.md` is the current repository status summary and must remain consistent with that framework.

## Repository authority

- Repository: `tcmegahan/Crown2026`
- Visibility: private
- Default branch: `main`
- Public-facing product name: CROWN
- Operating state: bounded remediation / no-go / hold

This is the sole authoritative CROWN engineering repository. Older repositories, historical branches, archived reports, generated evidence, and superseded status records do not override #1619, current exact-SHA GitHub evidence, deployed-runtime evidence, or the current repository status summary.

## Start here

1. [Eight-lane production-readiness program](https://github.com/tcmegahan/Crown2026/issues/1619)
2. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
3. [Repository Manifest](docs/canonical/REPOSITORY_MANIFEST.md)
4. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
5. [Developer Setup](docs/engineering/DEV_SETUP.md)
6. [Architecture](docs/architecture/)
7. [Operations](docs/operations/README.md)
8. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
9. [Security Policy](SECURITY.md)

## Repository contents

The active tree is limited to application source, migrations, active tests, build and dependency configuration, CI and deployment definitions, and current architecture, engineering, security, operations, provenance, ownership-transfer, and release-authority documentation.

Generated audit output, test-result dumps, copied evidence packs, dated completion boards, demo scripts, marketing material, transaction strategy, cleanup working notes, historical archives, and retired automation are intentionally excluded from the active tree.

## Security and data rules

Never commit passwords, API keys, tokens, production environment files, real school data, production database dumps, private certificates, tenant secrets, Microsoft credentials, payment credentials, recovery codes, or confidential communications.

Sandbox data must be synthetic and clearly labeled. Historical material containing sensitive information must not be distributed as a clean diligence artifact.

## Ownership and provenance

CROWN was created and developed primarily by TC Megahan as a solo developer, with limited support from two collaborators. TC served as Founder/Product Owner, principal product designer, architecture and workflow authority, primary developer, acceptance authority, and release authority.

Commercially available development and automated-assistance tools were used as engineering aids. They are not product owners, authorship authorities, independent reviewers, release authorities, or runtime dependencies. The controlled provenance record is `docs/provenance/CROWN_DEVELOPMENT_PROVENANCE.md`.

Current ownership, administrator authority, `CODEOWNERS`, external services, domains, cloud resources, secrets, and operating responsibility must be updated through the controlled process in `docs/ownership/OWNER_HANDOFF.md`.

## Change control during remediation

Only narrowly scoped preservation, security containment, factual documentation correction, authorized blocker remediation, or owner-authorized hygiene changes are permitted. Selection of an immutable release candidate occurs only after all authorized repository-changing work is merged and the repository freeze is explicitly re-established. Production authorization then requires completion of all eight lanes on that unchanged SHA, current exact-commit verification, operational recovery proof, legal and compliance disposition, and a new GO/NO-GO decision.
