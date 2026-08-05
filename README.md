# CROWN

Christian School Management Solution

> **Certified release notice — August 4, 2026**
>
> CROWN completed bounded repository and production certification for release source `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`, immutable tag `prod-deploy-20260804-17573fb`, and deployment run `30944978175`. GitHub issue #1619 is the final controlling release and owner-handoff record. External payment processing remains disabled, must fail closed, and is deferred to a future owner.

## Repository authority

- Repository: `tcmegahan/Crown2026`
- Visibility: private
- Default branch: `main`
- Public-facing product name: CROWN
- Certified production source: `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`
- Immutable production tag: `prod-deploy-20260804-17573fb`
- Current operating state: certified bounded production release; buyer-specific transfer actions pending an identified buyer

This is the sole authoritative CROWN engineering repository. Older repositories, historical branches, archived reports, generated evidence, and superseded status records do not override issue #1619, the immutable production tag, exact-SHA GitHub evidence, deployed-runtime evidence, or `docs/CURRENT_RELEASE_STATUS.md`.

## Start here

1. [Final release and owner-handoff record](https://github.com/tcmegahan/Crown2026/issues/1619)
2. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
3. [Repository Manifest](docs/canonical/REPOSITORY_MANIFEST.md)
4. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
5. [Developer Setup](docs/engineering/DEV_SETUP.md)
6. [Architecture](docs/architecture/)
7. [Operations](docs/operations/README.md)
8. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
9. [Security Policy](SECURITY.md)

## Repository contents

The active tree is intended to contain application source, migrations, active tests, build and dependency configuration, CI and deployment definitions, and current architecture, engineering, security, operations, provenance, ownership-transfer, and release-authority documentation.

Generated audit output, test-result dumps, copied evidence packs, dated completion boards, demo scripts, marketing material, transaction strategy, cleanup working notes, historical archives, and retired automation do not belong in the active tree unless an active workflow or controlled diligence record explicitly requires them.

## Security and data rules

Never commit passwords, API keys, tokens, production environment files, real school data, production database dumps, private certificates, tenant secrets, Microsoft credentials, payment credentials, recovery codes, or confidential communications.

Sandbox data must be synthetic and clearly labeled. Historical material containing sensitive information must not be distributed as a clean diligence artifact.

The historically exposed Ed25519 key is permanently retired and prohibited from use. Its replacement private key must remain outside Git. Historical Git rewriting remains deferred unless a buyer, insurer, auditor, counsel, or binding compliance obligation specifically requires it.

## Ownership and provenance

CROWN was created and developed primarily by TC Megahan as a solo developer, with limited support from two collaborators. TC served as Founder/Product Owner, principal product designer, architecture and workflow authority, primary developer, acceptance authority, and release authority.

Commercially available development and automated-assistance tools were used as engineering aids. They are not product owners, authorship authorities, independent reviewers, release authorities, or runtime dependencies. The controlled provenance record is `docs/provenance/CROWN_DEVELOPMENT_PROVENANCE.md`.

Current ownership, administrator authority, `CODEOWNERS`, external services, domains, cloud resources, secrets, and operating responsibility must be updated through the controlled process in `docs/ownership/OWNER_HANDOFF.md`.

## Post-release change control

The certified production identity remains the immutable tag and source listed above. Documentation, hygiene, and architecture-hardening changes after that tag do not silently redefine the deployed release.

Post-release changes must be narrowly scoped, evidence-based, reviewed through a branch and pull request, and validated according to affected risk. Delete or consolidate a tracked item only after proving that active imports, routes, workflows, tests, migrations, deployment paths, documentation links, and runtime consumers do not depend on it.

Buyer-specific account creation, credential transfer, access removal, contracts, and payment-provider activation remain transaction actions and must not be represented as completed before an identified buyer accepts them.
