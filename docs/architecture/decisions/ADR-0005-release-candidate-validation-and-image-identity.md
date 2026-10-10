# ADR-0005: Validate release candidates before production mutation

Status: PROPOSED / NOT ACCEPTED. Implementation and decision acceptance remain pending governed review.
Owner: CROWN product owner. Authorization: October 9, 2026 instruction to implement CI hardening.
Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.

## Context and decision

Previously, release resolution led directly to production migrations before image build,
scan and tests. Production entrypoints also differed: dispatch published before scanning,
and its image scan lacked an explicit blocking exit code. Image references used source-SHA
tags rather than byte identities.

The proposed implementation makes both entrypoints resolve the candidate, run complete governed backend coverage and
frontend tests/build, build one image locally, block high/critical image findings, publish
that validated image, and resolve its registry digest. Only successful candidate validation
permits production migration. Deployment consumes that same digest and checks the Azure
configured digest independently from the runtime's full source SHA.

Deployment never rebuilds the candidate or updates a `latest` alias. Existing production
concurrency, migration locking, freeze controls, environment protection and credential
compatibility remain in place. Write scopes are job-specific rather than inherited by
release resolution. Coverage retains the existing reviewed boundary and 75% threshold.

## Alternatives

Keeping migration first risks database mutation for a rejected application candidate.
Adding a preflight but rebuilding afterward does not bind validation to deployed image bytes.
The chosen dependency chain preserves one validated image through deployment.

## Trust and compatibility

Registry publication is candidate staging, not application deployment. Failure of tests,
scan, publication, digest resolution or migration prevents downstream application deployment.
Registry authentication remains an existing environment dependency. Source gates do not
assert production execution or credential availability. No payments or providers are activated.

Signed provenance and digest-aware rollback remain separate follow-up controls.

## Validation and reversal

A required repository policy verifier rejects bypassed dependencies, skipped/nonblocking
scan steps, early publication, mutable deployment references and candidate rebuilding.
Mutation tests and the existing release workflow contracts must pass. Hosted workflow lint,
security checks, and exact-head CI are required before merge.

Rollback: revert this outcome PR. This source change does not execute a production migration
or deploy. Azure execution, actual digest identity and recovery remain NOT VERIFIED until an
explicit operational release is authorized and evidenced.
