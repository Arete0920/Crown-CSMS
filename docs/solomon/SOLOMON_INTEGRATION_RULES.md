# SOLOMON Integration Rules

Status: Planning Only

## Integration Principle

SOLOMON must integrate through read-only, feature-flagged interfaces first.

## Hard Rules

1. No direct production module dependency until SOLOMON APIs are tested.
2. No migrations touching existing onboarding tables during initial scaffold.
3. No removal of existing onboarding Solomon models until migration proof exists.
4. No write APIs in the first implementation pass.
5. No curriculum ingestion in the first implementation pass.
6. No Microsoft sync in the first implementation pass.
7. No autonomous content-generation or automated decision functionality.

## Feature Flag

Future implementation must use:

SOLOMON_ENABLED = False by default

## Initial API Direction

Future endpoints may include:

- GET /api/solomon/categories/
- GET /api/solomon/topics/
- GET /api/solomon/audiences/
- GET /api/solomon/articles/
- GET /api/solomon/playbooks/
- GET /api/solomon/context/

## Release Protection

SOLOMON work must not change release certification results unless intentionally included in a future gate.

## Optional adult guidance extension

The owner-authorized optional guidance slice is governed by
[Solomon AI privacy boundary](SOLOMON_AI_PRIVACY_BOUNDARY.md). Its structured POST
is read-only with respect to school operations and writes only an audit event.
It returns curated guidance and does not activate autonomous generation or
external AI. Existing first-pass resource APIs remain read-only.
