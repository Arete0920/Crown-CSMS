# ADR-0002 — Canonical Frontend API Transport

**Status:** Accepted  
**Date:** 2026-08-08  
**Owner:** CROWN Architecture Authority

## Context

CROWN has many role-aware frontend surfaces that call first-party APIs under authentication and school-tenant scope. Duplicating token lookup, tenant-header propagation, API-base selection, credentials, timeout handling, correlation IDs, status handling, and error normalization in feature modules creates inconsistent security and observability behavior.

The repository already contains a canonical transport in `frontend/dashboards/src/utils/authClient.js`, with converged wrappers and contract tests. Final handoff review identified residual protected direct-fetch consumers that must converge on this authority.

## Decision

`frontend/dashboards/src/utils/authClient.js` is the canonical transport authority for protected first-party CROWN API traffic.

Protected frontend modules must use `authenticatedFetch`, `authenticatedJson`, or a wrapper that delegates directly to those functions.

The canonical transport owns:

- configured API-base resolution;
- trusted first-party URL determination;
- access-token propagation;
- selected-school `X-School-Id` propagation;
- credential behavior;
- request timeout and cancellation;
- correlation-ID behavior;
- structured non-success failures;
- protection against forwarding CROWN auth/tenant context to untrusted external origins.

Feature modules must not reconstruct those responsibilities.

## Explicit exceptions

Direct browser `fetch` is permitted only when the call is deliberately outside the protected first-party transport contract, including:

1. authentication/bootstrap calls that occur before an access token exists;
2. public sandbox invitation/session bootstrap endpoints whose access contract is intentionally unauthenticated or invite-bound;
3. explicitly public admissions, giving, ticket-purchase, or other public-entry endpoints;
4. development-only diagnostic tooling;
5. calls to non-CROWN external origins that must never receive CROWN authentication or school-tenant headers;
6. tests and certification harnesses exercising browser/network behavior directly.

Each exception must be identifiable from its module purpose and must not silently become a protected school-operational API client.

## Role and tenant authority

Client-supplied role headers are not an authorization authority. Role and school authorization derives from authenticated server-side identity, role membership, canonical tenant resolution, and backend permission enforcement.

The frontend may carry school selection context through `X-School-Id`; the backend remains responsible for validating that selection against the authenticated principal and any explicit override authority.

## Status and retry semantics

- The canonical transport fails non-success statuses by default.
- Feature code that intentionally interprets a non-2xx response may provide an explicit `validateStatus` policy.
- No global retry is permitted for mutating requests.
- Any retry must be operation-specific and safe under the endpoint's idempotency contract.

## Provenance rule

A dashboard or aggregate may be marked `live` only when the data required for that live state is complete under its defined contract. Partial live responses must not be merged with demo/fixture values and represented as one live aggregate.

## Enforcement

Tests must protect at least the following:

- canonical navigation/dashboard wrappers delegate to the canonical transport;
- Board Executive data uses canonical transport and all-or-nothing live provenance;
- deprecated duplicate transports do not return;
- newly identified protected direct-fetch consumers are migrated or explicitly classified as exceptions.

## Consequences

### Positive

- one security and tenant propagation policy;
- consistent timeout/error/correlation behavior;
- reduced cross-origin credential risk;
- easier API-base and identity changes for the successor owner;
- clearer distinction between public bootstrap traffic and authenticated operational traffic.

### Tradeoff

Public/bootstrap modules remain explicit exceptions rather than being forced through an authenticated client whose semantics do not apply.

## Reversal / replacement

Replacing the canonical transport requires a new ADR, a complete consumer inventory, same-head frontend and browser regression proof, and evidence that authentication, tenant, external-origin, timeout, correlation, and error semantics remain equivalent or stronger.
