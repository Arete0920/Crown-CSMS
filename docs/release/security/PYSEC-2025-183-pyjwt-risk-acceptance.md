# PYSEC-2025-183 PyJWT Risk Acceptance

Status: **retired on 2026-10-02**. An unfiltered `pip-audit 2.10.1 --strict` run against backend and load-test requirements completed with no known vulnerabilities. CI no longer ignores this advisory. The dated rationale below is historical and does not authorize future suppression.

Date: 2026-05-20

## Advisory

`pip-audit` reports `PYSEC-2025-183` against `pyjwt` even at `PyJWT==2.12.0`.

## Current dependency need

`pyjwt` is required through the authentication stack using `djangorestframework-simplejwt`.

## Fix availability

At the time of this release review, `pip-audit` reports no fixed version for this advisory.

## Release decision

This advisory is explicitly risk-accepted for the current release candidate because no fixed version is available and removing the JWT authentication dependency would be a larger architectural change.

## Follow-up requirement

Re-check this advisory before pilot/GA promotion. Remove the ignore rule immediately when a fixed version is published or when authentication is refactored.
