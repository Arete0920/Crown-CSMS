# Human Ownership and AI-Assistance Policy

**Status:** Canonical engineering governance  
**Owner:** TC Megahan, Founder/Product Owner  
**Related program:** #1432

## Purpose

This policy separates human product ownership, creator and architecture authority, collaborator involvement, automated assistance, technical verification, acceptance, and release authority in the CROWN repository.

An AI-pattern finding is a maintainability, verification, or provenance concern. It is not proof that an AI system authored a file, and it is not proof that a human contributor did or did not contribute.

## Human ownership and authority

### TC Megahan

TC Megahan is the creator of CROWN, Founder/Product Owner, principal developer, principal product designer, architecture authority, workflow designer, repository owner, requirements authority, technical-direction authority, acceptance authority, and release authority.

TC conceived and designed the platform architecture and operating/application workflows, directed implementation, performed product-development work, and remains accountable for the resulting product. TC is the sole code owner and sole repository maintainer for the development program. These authority and creation statements do not assert unsupported line-by-line typing provenance; where file-, module-, commit-, review-, testing-, or documentation-level attribution is material, the Contribution Evidence Ledger and durable repository evidence control.

### Founding and early collaborators

Anthony Rizzo, Ayush Agarwal, and Jed Hansen were founding/early collaborators in the CROWN program. Their early involvement may be stated as such. Specific implementation, design, documentation, review, testing, or other work must be attributed to an individual only when repository history, project records, correspondence, working documents, or other durable evidence supports that claim.

General early involvement must not be expanded into unsupported specific authorship, code ownership, architecture authority, acceptance authority, release authority, or intellectual-property ownership.

### New collaborators and prospective reviewers

Johnny Megahan and Evan Lesage are new collaborators designated for advisory repository review. No historical implementation, authorship, prior project accomplishment, completed review disposition, code ownership, architecture authority, acceptance authority, release authority, or intellectual-property ownership is assigned to either person unless later durable evidence supports that claim.

Repository access or review activity, when it occurs, does not by itself confer authorship, contribution status, product ownership, code ownership, or intellectual-property rights. Current access and completed-review status must be reported from repository evidence, not assumption.

## Development assistance

CROWN used numerous commercial development tools and interim coding assistants at different stages. Those tools and assistants may have supported bounded implementation, debugging, testing, analysis, documentation, code review, and repository operations. Active and external-facing materials should describe that assistance accurately and in vendor-neutral terms rather than attempting to name every interim tool or assistant.

Development assistants are not:

- product owners;
- requirements authorities;
- architecture owners;
- founders or co-founders;
- human authors or contributors;
- independent human reviewers;
- security approvers;
- acceptance authorities;
- release authorities.

Material automated assistance must be disclosed in the applicable pull request. Disclosure does not reduce the human owner's accountability for scope, correctness, verification, security, and acceptance.

## Required pull-request disclosure

Every non-trivial pull request must identify:

```text
Human owner:
Evidence-backed human contributors:
Development assistance:
Human verification:
Unverified attribution:
```

`Evidence-backed human contributors` must name only people whose contribution to that specific change is supported by durable evidence. Founding/early involvement alone is not sufficient to assign specific PR or file authorship. New or advisory collaboration is not code contribution unless evidence proves otherwise.

`Development assistance` should state `none`, `limited`, or `material` and briefly identify the assistance performed. Vendor or product names are not required unless needed for security, licensing, audit, or historical evidence.

`Human verification` must describe the actual review and validation performed. A list of commands that were not executed is not verification.

## Attribution integrity

The repository must not:

1. rewrite commit history to manufacture individual authorship;
2. infer authorship from coding style, comments, file naming, or apparent AI patterns;
3. identify a collaborator as a founder, co-founder, developer, code contributor, or code owner without Founder/Product Owner authorization and durable evidence appropriate to that claim;
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

A green automated check is evidence, but it is not product ownership, human authorship, independent human approval, or release authorization.

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

- TC Megahan's creator, principal-developer, design, architecture, workflow, product ownership, acceptance, and release authority;
- Anthony Rizzo, Ayush Agarwal, and Jed Hansen as founding/early collaborators, with specific work credited only where evidence supports it;
- Johnny Megahan and Evan Lesage as new/advisory collaborators with no historical contribution or prior-work credit unless later evidence supports it;
- development assistance;
- automated verification;
- human acceptance and release authority;
- unresolved or `NOT VERIFIED` attribution.

Specific named contribution claims must follow `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md` and its underlying durable evidence.