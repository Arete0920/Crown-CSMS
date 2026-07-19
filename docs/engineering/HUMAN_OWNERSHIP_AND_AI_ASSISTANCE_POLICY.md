# Human Ownership and AI-Assistance Policy

**Status:** Canonical engineering governance  
**Owner:** TC Megahan, Founder/Product Owner  
**Related program:** #1432

## Purpose

This policy separates human product ownership, evidence-backed contributor credit, automated assistance, technical verification, acceptance, and release authority in the CROWN repository.

An AI-pattern finding is a maintainability, verification, or provenance concern. It is not proof that an AI system authored a file, and it is not proof that a human contributor did not contribute.

## Human ownership and authority

### TC Megahan

TC Megahan is the Founder/Product Owner, repository owner, requirements authority, technical-direction authority, acceptance authority, and release authority for CROWN.

Those roles do not automatically establish that TC personally implemented every line of code. Specific implementation, review, testing, design, or documentation claims must still be supported by repository history or another retained record.

### Founding and early collaborators

Anthony Rizzo, Ayush Agarwal, and Jed Hansen are founding/early collaborators.

Specific credit for modules, files, architecture, implementation, testing, review, documentation, or operations must be supported by commits, pull requests, issue records, review records, project documents, signed records, or other durable evidence. Unsupported specific claims remain `NOT VERIFIED`.

### New collaborators

Johnny Megahan and Evan Lesage are new collaborators. No historical contribution or prior work may be assigned to them. Future contributions may be recorded when durable evidence exists.

## AI-assisted tooling

AI tools and development assistants may support bounded implementation, debugging, testing, analysis, documentation, code review, and repository operations.

They are not:

- product owners;
- requirements authorities;
- architecture owners;
- human authors or contributors;
- independent reviewers;
- security approvers;
- acceptance authorities;
- release authorities.

Material AI assistance must be disclosed in the applicable pull request. Disclosure does not reduce the human owner's accountability for scope, correctness, verification, security, and acceptance.

## Required pull-request disclosure

Every non-trivial pull request must identify:

```text
Human owner:
Evidence-backed contributors:
AI assistance:
Human verification:
Unverified attribution:
```

`AI assistance` should state `none`, `limited`, or `material` and briefly identify the assistance performed.

`Human verification` must describe the actual review and validation performed. A list of commands that were not executed is not verification.

## Attribution integrity

The repository must not:

1. rewrite commit history to manufacture individual authorship;
2. infer authorship from coding style, comments, file naming, or apparent AI patterns;
3. add contributor names solely to improve diligence presentation;
4. describe an automated review as independent human review;
5. conceal material use of development assistance;
6. convert `NOT VERIFIED` claims into definitive client-, buyer-, or future-owner-facing statements.

Submission metadata may identify the account, editor, connector, assistant, or automation that recorded work. It does not by itself prove who conceived, directed, implemented, reviewed, tested, or accepted that work.

## Verification and acceptance

Human verification must be proportional to risk and may include:

- final diff inspection;
- focused tests;
- broader contract or integration tests;
- security and tenant-isolation review;
- exact-head GitHub Actions evidence;
- runtime or operational evidence where applicable;
- documented disposition of review findings.

A green automated check is evidence, but it is not product ownership, human authorship, independent approval, or release authorization.

## Solo-maintainer control

When repository rules require review that the sole repository owner cannot independently provide, use `SOLO_DEVELOPER_APPROVED_WORKAROUND` only as a documented compensating control.

The workaround requires:

1. a bounded and reviewed scope;
2. an exact PR head SHA;
3. all applicable technical checks settled with `pending=0` and `failed=0`;
4. no unresolved actionable review thread or known defect;
5. a governance record identifying non-claims and residual risk;
6. a head-SHA-locked merge;
7. post-merge verification when the change affects runtime, deployment, security, tenant isolation, recovery, compliance, or release controls.

It must never override a failed technical, security, tenant, recovery, compliance, or release gate.

## External-use rule

Client-, buyer-, diligence-, and future-owner-facing materials must distinguish:

- product ownership;
- evidence-backed human contributions;
- automated assistance;
- automated verification;
- human acceptance and release authority;
- unresolved or `NOT VERIFIED` attribution.

The Contribution Evidence Ledger is the controlling record for specific contributor claims.