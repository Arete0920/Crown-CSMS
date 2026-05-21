# PYSEC-2024-271 Flask-Cors Risk Acceptance

Date: 2026-05-21

## Advisory

`pip-audit` reports `PYSEC-2024-271` / `CVE-2024-1681` against `flask-cors` while resolving `backend/requirements-loadtest.txt`.

## Current dependency need

`backend/requirements-loadtest.txt` exists to support load and release-readiness exercises through `locust`. Current resolution pulls `flask-cors==6.0.2` transitively.

## Fix availability

At the time of this release review, `pip-audit` reports no fixed version for this advisory, and package index metadata shows no release newer than `6.0.2`.

## Release decision

This advisory is temporarily risk-accepted for the current release candidate because no patched upstream version is available and removing the load-test toolchain would reduce release-readiness coverage.

## Follow-up requirement

Re-check this advisory before pilot or GA promotion. Remove the ignore rule immediately when a fixed upstream release is available or when the load-test stack is changed.
