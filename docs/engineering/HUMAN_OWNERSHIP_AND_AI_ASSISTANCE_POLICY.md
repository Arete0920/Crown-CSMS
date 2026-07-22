# Human Ownership and AI-Assistance Policy

**Status:** Canonical engineering governance  
**Owner:** TC Megahan, Founder/Product Owner  
**Related program:** #1432

## Purpose

This policy separates human product ownership, creator and architecture authority, evidence-backed contributor credit, automated assistance, technical verification, acceptance, and release authority in the CROWN repository.

An AI-pattern finding is a maintainability, verification, or provenance concern. It is not proof that an AI system authored a file, and it is not proof that a human contributor did not contribute.

## Human ownership and authority

### TC Megahan

TC Megahan is the creator of CROWN, Founder/Product Owner, principal product designer, architecture authority, workflow designer, repository owner, requirements authority, technical-direction authority, acceptance authority, and release authority.

TC designed the platform architecture and created the operating and application workflow that directed implementation. TC also performed implementation work and remains accountable for the resulting product. These authority and creation statements do not assert that TC personally authored every line of code. Specific line-level implementation, review, testing, or documentation claims should be supported by repository history or another retained record where such precision is required.

### Collaborators

Early, interim, and later collaborators supported portions of CROWN at different stages. Active repository documentation does not enumerate those individuals unless a present operational, legal, security, access-control, or evidence requirement makes identification necessary.

Specific credit for modules, files, architecture, implementation, testing, review, documentation, or operations must be supported by commits, pull requests, issue records, review records, project documents, signed records, or other durable evidence. Unsupported specific claims remain `NOT VERIFIED`.

## Development assistance

CROWN used numerous development tools and interim coding assistants at different stages. Those tools and assistants may have supported bounded implementation, debugging, testing, analysis, documentation, code review, and repository operations. Active and external-facing materials should describe that assistance accurately and in vendor-neutral terms rather than attempting to name every interim tool or assistant.

Development assistants are not:

- product owners;
- requirements authorities;
- architecture owners;
- founders or co-founders;
- human authors or contributors;
- independent reviewers;
- security approvers;
- acceptance authorities;
- release authorities.

Material automated assistance must be disclosed in the applicable pull request. Disclosure does not reduce the human owner's accountability for scope, correctness, verification, security, and acceptance.

## Required pull-request disclosure

Every non-trivial pull request must identify:

```text
Human owner:
Evidence-backed contributors:
Development assistance:
Human verification:
Unverified attribution:
```

`Development assistance` should state `none`, `limited`, or `material` and briefly identify the assistance performed. Vendor or product names are not required unless needed for security, licensing, audit, or historical evidence.

`Human verification` must describe the actual review and validation performed. A list of commands that were not executed is not verification.

## Attribution integrity

The repository must not:

1. rewrite commit history to manufacture individual authorship;
2. infer authorship from coding style, comments, file naming, or apparent AI patterns;
3. identify a collaborator as a founder or co-founder without explicit Founder/Product Owner authorization and durable evidence;
4. add contributor names solely to improve diligence presentation;
5. describe an automated review as independent human review;
6. conceal material use of development assistance;
7. convert `NOT VERIFIED` claims into definitive client-, buyer-, or future-owner-facing statements.

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

- TC Megahan's creator, design, architecture, workflow, product ownership, acceptance, and release authority;
- evidence-backed human contributions where identification is necessary and authorized;
- development assistance;
- automated verification;
- human acceptance and release authority;
- unresolved or `NOT VERIFIED` attribution.

The Contribution Evidence Ledger is the controlling record for specific contributor claims.