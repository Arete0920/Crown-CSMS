# SOLOMON Governance Corpus Schema 20260529

Status: Recommended intake schema
Scope: Rights-safe metadata and reference indexing only
Authority: Aligns with `docs/solomon/SOLOMON_GOVERNANCE_MODEL.md`, `docs/solomon/SOLOMON_INTEGRATION_RULES.md`, and `docs/solomon/SOLOMON_GOVERNANCE_CORPUS_WAVE_20260529.md`

## Purpose

This document defines the intake shape and review rules for SOLOMON governance corpus entries. It is intended to keep governance collections consistent, source-bound, and safe for rights-sensitive use.

## Required Fields

Every governance corpus entry should include the following fields:

- title
- slug
- summary
- category
- topic
- audience
- visibility
- status
- owner
- approver
- review_date
- version
- source_url
- license_type
- publisher
- school_scope
- created_at
- updated_at

## Recommended Values

### category

Use a stable corpus category such as:

- board governance
- board policy manuals
- christian school bylaws
- accreditation standards
- head of school governance
- strategic planning
- risk management
- committee structures
- school governance handbooks
- christian education leadership resources

### visibility

Use one of:

- internal
- review
- published

### status

Use one of:

- proposed
- review_pending
- approved
- published
- archived

### license_type

Use one of:

- public
- reference_only
- publisher_permission_required
- school_internal

## Intake Rules

1. Do not ingest non-governance content into this corpus wave.
2. Prefer official publisher, accreditor, association, school-board, or school handbook sources.
3. Record the exact source URL before approval.
4. Treat all records as reference-only unless a stronger rights posture is documented.
5. Do not promote a record to published without human review.
6. Do not duplicate curriculum text, devotional content, assessments, or teacher guides.
7. Do not mix governance corpus entries with onboarding, workflow, or release authority records.
8. Keep all records tenant-safe and source-attributed.

## Review Gates

An entry is eligible for approval when all are true:

- the source is identifiable and rights-safe
- the title and summary are governance-focused
- the category and topic match the corpus wave
- the license posture is documented
- the record is not a duplicate of an existing approved entry
- the owner and approver are assigned
- the review date is present

## Suggested Review Workflow

1. Propose the entry.
2. Capture source URL and rights posture.
3. Classify category, topic, and audience.
4. Set visibility to review.
5. Approve or archive after human review.
6. Publish only when the metadata record is complete and verified.

## Example Record Shape

```yaml
title: Board Governance Policy Manual
slug: board-governance-policy-manual
summary: Governance policy reference for board conduct and operating procedures.
category: board policy manuals
topic: board governance
audience: board members
visibility: review
status: proposed
owner: solomon-governance-team
approver: pending
review_date: 2026-06-05
version: 1.0
source_url: https://example.org/governance/policy-manual
license_type: reference_only
publisher: Example Publisher
school_scope: christian k-12
created_at: 2026-05-29T00:00:00Z
updated_at: 2026-05-29T00:00:00Z
```

## Validation Notes

- Keep records additive and reviewable.
- Preserve source traceability for every entry.
- Avoid automatic canonicalization until the governance corpus is mature.

## Relationship To The Governance Wave

The corpus wave defines what to collect.
This schema defines how to collect and govern it.

Together they provide a safe foundation for SOLOMON governance lookup, review, and future provenance work.
