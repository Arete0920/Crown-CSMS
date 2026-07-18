# CI Duplicate Analysis Worksheet

Related: #1394 and #1374

## Initial clusters

1. Python execution: Tests, CI Tests and Checks, pytest-gate, backend-gate, tenant and domain gates.
2. Frontend execution: dashboard build, route gate, UI proof, sandbox evidence, and proof ceremonies.
3. Release authority: Release Verify, Release Scorecard, RC promotion, Release Authority, Proof Ceremony, and runtime ceremony.
4. Security and dependencies: dependency review, audit, scan, secret scan, CodeQL, license, and public-repository quality checks.
5. Governance: spine audit, claims guard, PR hygiene, workflow policy, and release-document checks.

## Required fields for each workflow

- workflow file and displayed name
- trigger and path filter
- required, release-only, scheduled, evidence-only, or advisory status
- major commands and dependencies
- artifacts and retention
- concurrency and cancellation behavior
- unique supported claim
- duplicated commands
- branch-protection dependency
- keep, consolidate, replace, or retire disposition

## Change rule

No required check is removed or renamed until branch-protection usage and command-level equivalence are proven. Consolidation proceeds one low-risk cluster at a time while preserving failure localization and exact-SHA evidence.
