# CROWN DEV Redis control-plane inventory (read-only)

Issue: #427. This helper inspects the **existing Azure Managed Redis Balanced B0** DEV Redis, private endpoint, private DNS, and App Service configuration. It creates or changes nothing and must not be represented as hosted release certification.

In an operator-controlled Azure CLI session with permission to read the reviewed CROWN DEV subscription:

```powershell
$env:CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID = '<independently verified subscription GUID>'
python scripts/ops/verify_dev_redis_controlplane.py
Remove-Item Env:CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID
```

The script uses core Azure CLI `az resource show` and an explicit ARM GET for `databases/default`, pinned to API `2025-07-01`; it needs no RedisEnterprise CLI extension and never falls back to Classic `az redis show` Basic/C0. It checks the expected East US cluster, default database settings, Managed Redis private-link target, and region-qualified private DNS A record. It fails closed on inconsistent or missing metadata and never retrieves Redis database keys.

The output deliberately contains only classifications, not Azure resource IDs, setting values, credentials, or raw CLI errors. The command fails closed if the selected subscription does not match or projected resource reads are unavailable. Exit 0 means the selected metadata is internally consistent, **not** that the app can authenticate to Redis. Exit 2 indicates blocked/unavailable checks.

Offline unit tests: `python -m unittest discover -s scripts/ops -p test_verify_dev_redis_controlplane.py -v`.

Do not reprovision the Redis instance already reported created. Further acceptance requires effective secret and Key Vault resolution, validated app subnet and DNS reachability, TLS connectivity, actual shared counters across workers with HTTP 429, fail-closed HTTP 503 during a controlled outage, and exact deployed source SHA. Coordinate these checks with the active Azure operator workstream. Never close #427 based only on this inventory.

## Approved resource type and database

The expected target follows the [recorded DEV configuration and owner approval](https://github.com/Arete0920/Crown-CSMS/issues/427#issuecomment-6419888463):
`Microsoft.Cache/redisEnterprise/crown-auth-cache-dev` in East US,
`Balanced_B0`, with high availability disabled for the approved single-node DEV
configuration. It is **not** Classic `Microsoft.Cache/Redis` Basic/C0. The
collector must not fall back to, recreate or substitute a Classic cache if the
Managed Redis resource cannot be read.

The cluster is read through `az resource show` with explicit resource type and
API version `2025-07-01`. The `databases/default` child is read with an explicit
ARM GET on the same pinned subscription and API version. Both must report
successful provisioning and a running resource. Expected settings are public
access disabled, TLS 1.2, and an encrypted database on port 10000 with
`NoCluster` and `NoEviction`. Missing, unavailable or inconsistent properties
block the inventory; no configuration change is attempted.

Microsoft documents these separate resource schemas:
[Managed Redis cluster](https://learn.microsoft.com/en-us/azure/templates/microsoft.cache/2025-07-01/redisenterprise)
and [Managed Redis database](https://learn.microsoft.com/en-us/azure/templates/microsoft.cache/2025-07-01/redisenterprise/databases).
The private endpoint must target that Managed Redis resource ID, not a
same-named Classic resource. This is the **expected configuration**, not a claim
that actual Azure properties were independently observed.

No access-key operation is supported. App-setting names are projected by Azure
CLI; values and raw CLI errors are never printed or retained in the report.
Operator access and live inventory execution remain separate prerequisites.
