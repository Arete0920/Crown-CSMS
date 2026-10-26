"""Offline contracts for a read-only DEV Redis control-plane inventory."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("probe", Path(__file__).with_name("verify_dev_redis_controlplane.py"))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SUB = "11111111-2222-3333-4444-555555555555"
VNET = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Network/virtualNetworks/dev-vnet"
CACHE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Cache/redisEnterprise/crown-auth-cache-dev"
ZONE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Network/privateDnsZones/privatelink.redis.azure.net"

def sample():
    return {
        "redis": dict(state="Succeeded", public="Disabled", tls="1.2", sku="Balanced_B0", location="eastus"),
        "redis_database": dict(state="Succeeded", client="Encrypted", clustering="NoCluster", eviction="NoEviction", port=10000),
        "private_endpoint": dict(state="Succeeded", subnet=VNET + "/subnets/private", connections=[dict(target=CACHE, status="Approved", groups=["redisEnterprise"])]),
        "dns_zone_groups": [dict(state="Succeeded", zones=[ZONE])],
        "dns_vnet_links": [dict(state="Succeeded", vnet=VNET)],
        "dns_a_records": [dict(name="crown-auth-cache-dev.eastus", count=1)],
        "app_vnet": [dict(subnet=VNET + "/subnets/app", vnet=VNET)],
        "app_setting_names": ["CROWN_CACHE_URL"],
    }

class RedisReadOnlyTests(unittest.TestCase):
    def test_clean_metadata_not_release_certification(self):
        report = probe.evaluate(SUB, sample())
        self.assertEqual(report["control_plane_metadata"], "CONSISTENT")
        self.assertEqual(report["release_certification"], "NOT_VERIFIED")
        self.assertEqual(report["hosted_redis_connectivity"], "NOT_TESTED")

    def test_unsafe_and_missing_metadata_block(self):
        for name, replacement in [
            ("redis", dict(sample()["redis"], public="Enabled")),
            ("redis", dict(sample()["redis"], sku="Basic")),
            ("redis_database", dict(sample()["redis_database"], client="Plaintext")),
            ("redis_database", dict(sample()["redis_database"], eviction="AllKeysLRU")),
            ("redis_database", dict(sample()["redis_database"], port=6380)),
            ("private_endpoint", dict(state="Succeeded", subnet=VNET+"/subnets/private", connections=[])),
            ("dns_zone_groups", []), ("dns_vnet_links", []), ("dns_a_records", []),
            ("dns_a_records", [dict(name="crown-auth-cache-dev", count=1)]),
            ("app_vnet", []), ("app_setting_names", []),
        ]:
            with self.subTest(name=name):
                values = sample()
                values[name] = replacement
                self.assertEqual(probe.evaluate(SUB, values)["control_plane_metadata"], "BLOCKED")

    def test_managed_redis_cli_resource_and_private_link_contract(self):
        commands = {name: cmd for name, cmd, _ in probe.READS}
        self.assertEqual(commands["redis"][:2], ("redisenterprise", "show"))
        self.assertEqual(commands["redis_database"][:3], ("redisenterprise", "database", "show"))
        self.assertEqual(commands["dns_a_records"][4], "list")
        report = probe.evaluate(SUB, sample())
        self.assertEqual(report["checks"]["redis_database"], "CONSISTENT")
        mismatch = sample()
        mismatch["private_endpoint"]["connections"][0]["target"] = CACHE.replace("redisEnterprise", "Redis")
        self.assertEqual(probe.evaluate(SUB, mismatch)["checks"]["private_endpoint"], "BLOCKED")

    def test_unavailable_reads_block(self):
        for name, _, _ in probe.READS:
            with self.subTest(name=name):
                values = sample()
                values[name] = None
                self.assertEqual(probe.evaluate(SUB, values)["control_plane_metadata"], "BLOCKED")

    def test_wrong_subscription_does_not_read_resources(self):
        calls = []
        def read(args, query, *, subscription=None):
            calls.append((args, subscription))
            return "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        self.assertEqual(probe.collect(SUB, read=read)["reason"], "AZURE_SUBSCRIPTION_MISMATCH_OR_UNAVAILABLE")
        self.assertEqual(len(calls), 1)

    def test_every_read_uses_pinned_subscription(self):
        values = sample()
        calls = []
        def read(args, query, *, subscription=None):
            calls.append((args, subscription, query))
            if args == ("account", "show"):
                return SUB
            return values[next(name for name, cmd, _ in probe.READS if cmd == args)]
        self.assertEqual(probe.collect(SUB, read=read)["preflight"], "CONSISTENT")
        self.assertEqual(len(calls), len(probe.READS) + 1)
        self.assertTrue(all(call[1] == SUB for call in calls[1:]))

    def test_cli_fail_closed_does_not_expose_error(self):
        bad = lambda *args, **kwargs: Mock(returncode=1, stdout="private", stderr="secret")
        self.assertIsNone(probe.azure_read(("redisenterprise", "show"), "sku.name", subscription=SUB, runner=bad))

    def test_workflow_wires_offline_tests_and_restricted_oidc_inventory(self):
        workflow = (Path(__file__).resolve().parents[2]
                    / ".github/workflows/azure-classroom-preflight.yml").read_text(encoding="utf-8")
        self.assertIn("run: python -m unittest discover -s scripts/ops -p test_verify_dev_redis_controlplane.py -v", workflow)
        self.assertIn("inputs.dev_redis_controlplane_precheck != true", workflow)
        self.assertIn("dev-redis-controlplane-precheck:", workflow)
        section = workflow.split("  dev-redis-controlplane-precheck:\n", 1)[1]
        self.assertIn("github.ref == 'refs/heads/main'", section)
        self.assertIn("inputs.dev_redis_controlplane_precheck == true", section)
        self.assertIn("inputs.dev_owner_runtime_precheck != true", section)
        self.assertIn("environment: production", section)
        self.assertIn("id-token: write", section)
        self.assertIn("persist-credentials: false", section)
        self.assertIn("verify_dev_redis_controlplane.py", section)
        self.assertIn("CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}", section)
        self.assertIn("if-no-files-found: warn", section)
        self.assertNotIn("az webapp config appsettings set", section)
        self.assertNotIn("az redis create", section)
        self.assertNotIn("az deployment group create", section)

if __name__ == "__main__":
    unittest.main()
