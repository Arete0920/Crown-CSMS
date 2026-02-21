# RC1 Promotion Packet — v0.4.0-rc1

Tag: v0.4.0-rc1
Commit: 80e22fe79ea55c69e68b0cb2712c10ae6dc00f9c
PR: #298 (MERGED)
Checks: 29/29 green
Release object: exists (GitHub Releases)

Captured immutable runtime proof:

## git show -s --decorate v0.4.0-rc1

```text
commit 80e22fe79ea55c69e68b0cb2712c10ae6dc00f9c (tag: v0.4.0-rc1, origin/main, main)
Author: tcmegahan <tc.megahan@gmail.com>
Date:   Sat Feb 21 13:56:47 2026 -0500

		rc: promote rc/crown-0.4.0 -> main (v0.4.0-rc1) (#298)
```

## gh release view v0.4.0-rc1 --repo tcmegahan/Crown2026

```text
v0.4.0-rc1
tcmegahan released this about 13 minutes ago

Release Candidate 1 (RC1)
View on GitHub: https://github.com/tcmegahan/Crown2026/releases/tag/v0.4.0-rc1
```

## Azure health (dev)
GET https://crown-api-dev.azurewebsites.net/api/health/

```json
{
	"ok": true,
	"status": "ok",
	"demo_mode": false,
	"build_sha": "6f01abbdd0f88b18a00f0c39df86133bc7a4faa7",
	"env": "dev",
	"build_time_utc": "2026-02-21T19:21:11.133003+00:00",
	"version": "crown-0.3.0",
	"db": "ok"
}
```

- build_sha: 6f01abbdd0f88b18a00f0c39df86133bc7a4faa7
- db: ok

## Latest workflows
- deploy-dev: Dev Deploy (rc/**)
- rc-tier1-deployed-smoke: rc-tier1-deployed-smoke
- rc-promotion-gate: rc-promotion-gate
- promotion workflow present: Production Deploy
