# Production Incident Closure Evidence

Generated: 2026-05-11 02:01:44 -04:00

Repository: tcmegahan/Crown2026  
Base branch: main  
Base SHA: c8b6a24231ed2b6ad340a19c5c9b0f86649660bd  

## Production Health

Endpoint: https://crown-api-prod.azurewebsites.net/api/health/

Result:

- HTTP: 200
- env: prod
- status: ok
- ok: True
- db: ok
- version: crown-0.4.0-rc1
- build_sha: 500ec09461d583eaf309a852df16d510fb334c81
- deploy_tag: 
- deploy_run_id: 25528614282
- deploy_workflow: Production Deploy

## Target Incidents

- #795: OPEN - [INCIDENT] Prod deploy failed and rollback executed (2026-05-07T19:17:57.107Z)
- #796: OPEN - [INCIDENT] Prod deploy failed and rollback executed (2026-05-07T19:54:29.335Z)
- #797: OPEN - [INCIDENT] Prod deploy failed and rollback executed (2026-05-07T23:07:38.118Z)
- #798: OPEN - [INCIDENT] Prod deploy failed and rollback executed (2026-05-07T23:47:20.549Z)

## Recent Production Workflow Runs

- run 25652012372: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-11T05:26:03Z / https://github.com/tcmegahan/Crown2026/actions/runs/25652012372
- run 25649244778: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-11T03:47:56Z / https://github.com/tcmegahan/Crown2026/actions/runs/25649244778
- run 25646997236: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-11T02:23:01Z / https://github.com/tcmegahan/Crown2026/actions/runs/25646997236
- run 25645255591: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-11T01:16:07Z / https://github.com/tcmegahan/Crown2026/actions/runs/25645255591
- run 25643501493: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-11T00:05:18Z / https://github.com/tcmegahan/Crown2026/actions/runs/25643501493
- run 25642858505: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-10T23:34:16Z / https://github.com/tcmegahan/Crown2026/actions/runs/25642858505
- run 25642269476: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-10T23:05:17Z / https://github.com/tcmegahan/Crown2026/actions/runs/25642269476
- run 25641554853: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-10T22:30:45Z / https://github.com/tcmegahan/Crown2026/actions/runs/25641554853
- run 25640990944: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-10T22:03:52Z / https://github.com/tcmegahan/Crown2026/actions/runs/25640990944
- run 25640356681: Production Health Watch / Production Health Watch / status=completed / conclusion=success / created=2026-05-10T21:33:14Z / https://github.com/tcmegahan/Crown2026/actions/runs/25640356681

## Determination

Production runtime is currently healthy.

Open incident issues are eligible to close only as incident records if and only if:
1. production health remains HTTP 200,
2. response reports env=prod,
3. response reports db=ok,
4. issue bodies are preserved,
5. closure comment links this evidence,
6. release readiness is not upgraded by closing incidents alone.

Final release readiness remains separately gated by release evidence PR merge state, required checks, security update state, and branch/ruleset enforcement proof.
