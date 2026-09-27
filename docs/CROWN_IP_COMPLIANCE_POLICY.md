# CROWN Developer IP Compliance Policy

**Document Class:** Engineering Policy / Developer Onboarding  
**Owner:** Engineering Leadership  
**Applies to:** All engineers, contractors, interns, and contributors to the CROWN repository

## Purpose

Protect CROWN's intellectual-property integrity and ensure contributions are independently designed, evidence-backed, and free of proprietary third-party material.

## 1. No named competitors in repository content

Do not commit competitor or competing-product names in:

- source files;
- documentation;
- comments;
- examples;
- committed scripts;
- test fixtures;
- branch-specific committed configuration;
- migration guides;
- comparison matrices.

Use neutral terminology such as:

- legacy source system;
- third-party SIS;
- external billing platform;
- school-management platform;
- education software vendor.

## 2. No imitation language

Do not describe CROWN work as copied from, modeled after, cloned from, inspired by, or equivalent to a named external product.

Requirements must be expressed through:

- school workflows;
- user needs;
- accepted standards;
- CROWN's own domain model;
- security and compliance requirements;
- independent engineering judgment.

## 3. No reverse engineering

Do not:

- inspect proprietary database schemas;
- decompile commercial applications;
- intercept private application traffic;
- scrape authenticated commercial systems;
- replicate proprietary screen structures or internal behavior;
- copy non-public documentation or implementation artifacts.

Public market awareness may inform problem discovery, but CROWN implementation must be independently designed.

## 4. No proprietary language reuse

Use generic industry terminology and CROWN-specific product language. Do not import another vendor's proprietary labels, workflow names, or trade dress into CROWN.

## 5. Independent design

CROWN architecture and implementation must be traceable to:

- documented business requirements;
- canonical architecture decisions;
- accepted engineering patterns;
- statutory/regulatory requirements where applicable;
- accounting/security/data-governance principles;
- direct school-user needs.

## 6. Copyright and ownership

New source remains subject to CROWN's applicable ownership and contribution policies. Ownership claims must be supported by durable evidence.

## 7. Third-party dependencies

Before adding dependencies:

1. verify license compatibility;
2. record the dependency through the supported package manager;
3. pin or lock versions as required by repository policy;
4. do not fork or embed third-party source without review;
5. preserve required notices.

## 8. Mechanical repository scan

At release gates, scan committed source and documentation for:

- known competitor/vendor names;
- direct-comparison phrases;
- imitation language;
- copied proprietary terminology.

Any genuine hit must be removed or neutralized before merge.

Exclude only third-party dependency directories, generated caches, virtual environments, and other uncommitted/generated material that is not part of the repository source tree.

## 9. Violation handling

| Finding | Required response |
|---|---|
| Accidental named competitor reference | Remove before merge |
| Direct imitation/comparison wording | Rewrite from first principles |
| Copied proprietary UI/content | Redesign/remove and escalate |
| Evidence of reverse engineering | Escalate to legal/owner immediately |
| Deliberate proprietary code reuse | Block contribution and escalate |

## 10. Contributor acknowledgment

Contributors must understand and follow this policy before making substantive changes.

When uncertain about third-party IP boundaries, stop and obtain owner/legal review.
