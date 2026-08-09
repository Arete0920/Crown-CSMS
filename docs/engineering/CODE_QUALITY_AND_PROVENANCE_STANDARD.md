# Code Quality and Provenance Standard

**Status:** Canonical engineering standard  
**Owner:** CROWN Engineering

## Purpose

This standard governs maintainability, verification, provenance, and repository-hygiene findings without inferring authorship from code style or automation output.

## Review classes

- temporary, urgency, or unsupported outcome-claiming names;
- machine-specific paths or environment assumptions;
- embedded verdicts not calculated from current evidence;
- broad exception handling that suppresses required failures;
- mixed-responsibility scripts or modules;
- redundant narrative and duplicate authority documents;
- placeholder or sample behavior in runtime paths;
- duplicated wrappers and speculative abstractions;
- generated or copied repository debris;
- unproven attribution claims;
- unbounded or non-diagnostic automation.

## Rules

1. Preserve behavior unless an approved change authorizes otherwise.
2. Use current repository evidence.
3. Keep one coherent outcome in one pull request.
4. Search active references and replacement paths before deletion or rename.
5. Fail closed and retain diagnostic context.
6. Remove stale candidate lists when work is completed.
7. Mark unsupported conclusions `NOT VERIFIED`.
8. Do not use quality patterns as proof of authorship.

There is no standing candidate list in this document. Current findings must be supported by a fresh repository inspection and tracked in the applicable issue or pull request.
