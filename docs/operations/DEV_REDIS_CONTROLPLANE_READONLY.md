# CROWN DEV Redis control-plane inventory (read-only)

Issue: #427. This helper inspects the **existing** Azure DEV Redis, private endpoint, private DNS, and App Service configuration. It creates or changes nothing and must not be represented as hosted release certification.

In an operator-controlled Azure CLI session with permission to read the reviewed CROWN DEV subscription:

```powershell
$env:CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID = '<independently verified subscription GUID>'
python scripts/ops/verify_dev_redis_controlplane.py
Remove-Item Env:CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID
```

The output deliberately contains only classifications, not Azure resource IDs, setting values, credentials, or raw CLI errors. The command fails closed if the selected subscription does not match or projected resource reads are unavailable. Exit 0 means the selected metadata is internally consistent, **not** that the app can authenticate to Redis. Exit 2 indicates blocked/unavailable checks.

Offline unit tests: `python -m unittest discover -s scripts/ops -p test_verify_dev_redis_controlplane.py -v`.

Do not reprovision the Redis instance already reported created. Further acceptance requires effective secret and Key Vault resolution, validated app subnet and DNS reachability, TLS connectivity, actual shared counters across workers with HTTP 429, fail-closed HTTP 503 during a controlled outage, and exact deployed source SHA. Coordinate these checks with the active Azure operator workstream. Never close #427 based only on this inventory.
