# Recovery and Transferability Checklist

Related: #1270, #1393, and #1374

## Recovery evidence

- identify failed candidate and last-known-good immutable identity
- record rollback decision and operator
- execute controlled application rollback exercise
- execute isolated database restore exercise or approved equivalent
- record start, decision, recovery, and verification timestamps
- calculate observed recovery time
- record recovery-point basis
- verify health, build identity, tenant isolation, and critical data checks after recovery
- record manual intervention and escalation triggers

## Clean-room evidence

- use a clean environment without founder-specific local files
- clone the authoritative repository at an exact SHA
- follow repository-controlled setup instructions only
- install from checked-in dependency manifests
- record every required configuration contract
- run focused and broad tests
- start backend and frontend
- verify tenant-scoped behavior
- make one bounded non-critical change through the documented workflow
- rehearse non-production deployment, rollback, and restore
- record undocumented dependencies and founder-only knowledge

This checklist does not claim that either exercise has passed.
