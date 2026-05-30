# Certification Expiry and Revalidation Cadence (2026-05-30)

Purpose: define expiry windows and revalidation cadence for certification evidence.

## Expiry Policy

- Security and readiness contract evidence: expires after 14 days.
- Authority and ownership validator evidence: expires after 14 days.
- Full candidate proof packet (end-to-end): expires after 7 days.
- Any evidence linked to a superseded candidate SHA expires immediately.

## Revalidation Cadence

- Daily: fast validator sweep (authority, readiness, ownership, naming/index checks).
- Twice weekly: targeted backend/frontend contract suites.
- Weekly: full certification packet refresh on active candidate SHA.
- On every candidate SHA change: immediate mandatory revalidation before any GO claim.

## Enforcement Rule

- Expired evidence cannot be used to support COMPLETE/PROVEN claims.
- Expired or superseded artifacts must be replaced or demoted to historical status.
