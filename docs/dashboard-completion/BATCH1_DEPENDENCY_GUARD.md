# Batch 1 Dashboard Dependency Guard

Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Parent issue: #1089
Batch 0 issue: #1090
Batch 0 PR: #1097
Governance issue: #1105

## Purpose

This document prevents Batch 1 dashboard implementation from starting before Batch 0 establishes the proof/control layer required for safe dashboard promotion.

## Batch 1 scope

Batch 1 planning scope only:

- attendance
- billing
- gradebook
- communications
- registrar
- school-administrator

## Current decision

Batch 1 product-code implementation is blocked.

Planning may continue, but no Batch 1 dashboard should be promoted beyond dependency planning until Batch 0 reaches the minimum control threshold below.

## Batch 0 minimum threshold before Batch 1 implementation

- [ ] Batch 0 owner assigned.
- [ ] Batch 0 independent reviewer assigned.
- [ ] PR #1097 leaves draft only after evidence gates are complete.
- [ ] dashboard-certification-center has truthful proof-state payloads.
- [ ] release-reliability does not claim GO without release authority.
- [ ] compliance-audit exposes proof gaps truthfully.
- [ ] Batch 0 runtime/browser proof attached.
- [ ] Batch 0 tenant proof complete.
- [ ] Batch 0 permission proof complete.
- [ ] Batch 0 evidence packets updated and reviewed.
- [ ] Batch 0 review threads resolved or dispositioned.

## Allowed Batch 1 planning work

- Inventory existing Batch 1 dashboard routes and templates.
- Draft data contracts without implementation claims.
- Identify source modules and API candidates.
- Identify required KPIs, alerts, queues, freshness expectations, sensitivity, and proof needs.
- Prepare issue checklists.

## Disallowed before Batch 0 threshold

- Batch 1 product-code implementation.
- Batch 1 matrix promotion.
- Batch 1 certification claim.
- Batch 1 runtime-proof claim.
- Any sandbox, pilot, production, or release GO claim.

## Non-claims

This document does not certify Batch 0 or Batch 1 dashboards.
This document does not approve sandbox, pilot, production, or release GO.
