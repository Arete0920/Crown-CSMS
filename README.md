# CROWN

Christian School Management Solution

## Current certified release

- Backend source: `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`
- Immutable production tag: `prod-deploy-20260808-ce12c95`
- Production deployment: [run 31287503791](https://github.com/tcmegahan/Crown2026/actions/runs/31287503791)
- Dashboard deployment and live certification: [run 31289219093](https://github.com/tcmegahan/Crown2026/actions/runs/31289219093)
- Dashboard deployment source: `a3f89db677857a220b322b3f1bf094b3fdef3fa2`
- Live certification: `18/18 PASS`, `0 FAIL`
- Post-certification observer-cleanup baseline (PR #1949): `ef9e1fa4f06d6600d60313059f35c0bb564f5a5b`
- Payment processing: disabled, fail closed, and deferred to a future owner

The certified backend, deployed dashboard source, and current development head are separate identities. Later commits do not inherit production certification automatically.

## Start here

1. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
2. [Final release and owner-handoff record](https://github.com/tcmegahan/Crown2026/issues/1619)
3. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
4. [Architecture Map](docs/architecture/ARCHITECTURE_MAP.md)
5. [Developer Setup](docs/engineering/DEV_SETUP.md)
6. [Operations](docs/operations/README.md)
7. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
8. [Security Policy](SECURITY.md)

## Repository standards

This repository contains active application source, tests, migrations, build and deployment controls, and current architecture, engineering, security, operations, and transfer documentation. Historical pull requests and commits remain engineering provenance but are not current operating instructions.

Use one pull request per coherent, independently reversible outcome. Keep corrections discovered during validation in that pull request unless they cross a genuinely independent risk or rollback boundary.

Never commit secrets, production data, private certificates, confidential communications, or payment credentials. Sandbox data must be synthetic and clearly labeled.

## Ownership

CROWN was created and directed by TC Megahan, Founder/Product Owner, principal developer, product designer, and architecture and workflow authority. Anthony Rizzo, Ayush Agarwal, and Jed Hansen were founding/early collaborators; specific work is credited only where durable evidence supports it. Johnny Megahan and Evan Lesage are new/advisory collaborators and are not assigned historical contributions.

Detailed attribution and development-process records are governed by the [Human Accountability and Development Assistance Policy](docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md) and the [Contribution Evidence Ledger](docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md).
