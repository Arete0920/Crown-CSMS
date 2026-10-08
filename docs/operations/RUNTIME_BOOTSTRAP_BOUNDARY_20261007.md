# Runtime bootstrap boundary — 2026-10-07

Status: repair implementation; exact-head checks and governed merge pending.

Administrator bootstrap reads environment values as data inside a dedicated
management command. No credential value is interpolated into executable Python.
A username and nonempty policy-compliant password are required. Production also
requires BOOTSTRAP_ADMIN=true. An existing inactive or non-administrator account
cannot be silently elevated or have its password reset by this operation.

SEED_DEMO, RUN_DEV_BOOTSTRAP, RUN_GOLDEN_PATH_BOOTSTRAP and CI_SMOKE_USERNAME are
rejected in production before startup reaches those mutation commands. Azure host
identity or an explicit production environment marker activates the restriction.
Normal production startup continues to verify schema currency without migration.

Initial affected proof: 17 tests passed, covering literal quoted credentials,
activation, non-administrator denial, idempotent privileged rotation, production
flag rejection, and schema-deployment contracts. Password-policy rejection is an
additional regression requiring the final exact-head suite. No deployment or
current secret rotation is asserted by this source change.

Before authorized bootstrap, set BOOTSTRAP_ADMIN=true and the existing
DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD values in the external secret/configuration
system. Remove bootstrap activation after the bounded operation. Never put actual
credentials in Git, PR descriptions, logs, or test evidence.

Control path: solo-maintainer policy, exact-head required checks, retained CI
artifacts and advisory engineering audit. Rollback: revert this coherent PR;
returning to interpolated startup code requires explicit security disposition.
