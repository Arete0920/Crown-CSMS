# Crown Core Canon

## Purpose
Define the non-negotiable platform foundation.

## Core responsibilities
- authentication
- RBAC
- tenant enforcement
- audit/event framework
- shared error handling
- shared backend patterns
- shared frontend shell rules
- release discipline

## Non-negotiables
- Core owns truth
- Core contracts must be stable before modules build against them
- no module may bypass tenant or permission enforcement
- no duplicate source of truth for identity or enrollment
