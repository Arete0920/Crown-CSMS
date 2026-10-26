"""Offline contracts for a read-only DEV Redis control-plane inventory."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("probe", Path(__file__).with_name("verify_dev_redis_controlplane.py"))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SUB = "11111111-2222-3333-4444-555555555555"
VNET = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Network/virtualNetworks/crown-vnet"
CACHE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Cache/redisEnterprise/crown-auth-cache-dev"
ZONE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Network/privateDnsZones/privatelink.redis.azure.net"

def sample():
    return {
        "redis": dict(type=probe.CACHE_TYPE, runtime="Running", ha="Disabled",
                      state="Succeeded", public="Disabled", tls="1.2", sku="Balanced_B0", location="eastus"),
        "redis_database": dict(type=probe.DATABASE_TYPE, runtime="Running",
                               state="Succeeded", client="Encrypted", clustering="NoCluster", eviction="NoEviction", port=10000),
        "private_endpoint": dict(state="Succeeded", subnet=VNET + "/subnets/db-subnet", connections=[dict(target=CACHE, status="Approved", groups=["redisEnterprise"])]),
        "dns_zone_groups": [dict(state="Succeeded", zones=[ZONE])],
        "dns_vnet_links": [dict(state="Succeeded", vnet=VNET)],
        "dns_a_records": [dict(name="crown-auth-cache-dev.eastus", count=1)],
        "app_vnet": dict(subnet=VNET + "/subnets/app-subnet"),
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
        self.assertEqual(commands["redis"][:2], ("resource", "show"))
        self.assertEqual(commands["redis_database"][:3], ("rest", "--method", "get"))
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
            return values[next(name for name, cmd, _ in probe.READS
                               if tuple(arg.format(subscription=SUB) for arg in cmd) == args)]
        self.assertEqual(probe.collect(SUB, read=read)["preflight"], "CONSISTENT")
        self.assertEqual(len(calls), len(probe.READS) + 1)
        self.assertTrue(all(call[1] == SUB for call in calls[1:]))

    def test_cli_fail_closed_does_not_expose_error(self):
        bad = lambda *args, **kwargs: Mock(returncode=1, stdout="private", stderr="secret")
        self.assertIsNone(probe.azure_read(("redisenterprise", "show"), "sku.name", subscription=SUB, runner=bad))

    def test_classic_redis_and_unapproved_cluster_settings_never_pass(self):
        for changes in (
            dict(type="Microsoft.Cache/Redis", sku="Basic"),
            dict(sku="Balanced_B1"), dict(ha="Enabled"),
            dict(location="westus"), dict(runtime="Creating"),
            dict(public=None), dict(tls="1.1"), dict(tls=1.2),
        ):
            with self.subTest(changes=changes):
                values = sample()
                values["redis"].update(changes)
                self.assertEqual(probe.evaluate(SUB, values)["checks"]["redis"], "BLOCKED")

    def test_unsafe_or_missing_database_properties_never_pass(self):
        for changes in (
            dict(type="Microsoft.Cache/Redis"), dict(client="Plaintext"),
            dict(port=6379), dict(port="10000"), dict(port=True),
            dict(clustering="OSSCluster"), dict(eviction="AllKeysLRU"),
            dict(runtime="Updating"), dict(state=None),
        ):
            with self.subTest(changes=changes):
                values = sample()
                values["redis_database"].update(changes)
                self.assertEqual(probe.evaluate(SUB, values)["checks"]["redis_database"], "BLOCKED")
        values = sample()
        del values["redis_database"]
        self.assertEqual(probe.evaluate(SUB, values)["control_plane_metadata"], "BLOCKED")

    def test_private_endpoint_cannot_point_to_classic_same_name_cache(self):
        values = sample()
        values["private_endpoint"]["connections"][0]["target"] = CACHE.replace(
            "/redisEnterprise/", "/Redis/")
        report = probe.evaluate(SUB, values)
        self.assertEqual(report["checks"]["private_endpoint"], "BLOCKED")
        self.assertEqual(report["control_plane_metadata"], "BLOCKED")

    def test_only_the_approved_app_and_endpoint_subnets_pass(self):
        for name, changes in (
            ("private_endpoint", dict(subnet=VNET + "/subnets/app-subnet")),
            ("private_endpoint", dict(subnet=VNET.replace("crown-vnet", "other-vnet") + "/subnets/db-subnet")),
            ("app_vnet", dict(subnet=VNET + "/subnets/db-subnet")),
            ("app_vnet", dict(subnet=VNET.replace("crown-vnet", "other-vnet") + "/subnets/app-subnet")),
        ):
            with self.subTest(name=name, changes=changes):
                values = sample()
                values[name].update(changes)
                self.assertEqual(probe.evaluate(SUB, values)["checks"][name], "BLOCKED")

    def test_managed_gets_use_explicit_type_api_and_default_database(self):
        values = sample()
        calls = []
        def read(args, query, *, subscription=None):
            calls.append((args, subscription, query))
            if args == ("account", "show"):
                return SUB
            return values[next(name for name, cmd, _ in probe.READS
                               if tuple(arg.format(subscription=SUB) for arg in cmd) == args)]
        self.assertEqual(probe.collect(SUB, read=read)["preflight"], "CONSISTENT")
        cluster_args = calls[1][0]
        self.assertEqual(cluster_args[:2], ("resource", "show"))
        self.assertIn(probe.CACHE_TYPE, cluster_args)
        self.assertIn(probe.API_VERSION, cluster_args)
        database_args = calls[2][0]
        self.assertEqual(database_args[:3], ("rest", "--method", "get"))
        self.assertEqual(database_args[-1],
                         "https://management.azure.com" + CACHE
                         + "/databases/default?api-version=" + probe.API_VERSION)
        for args, _, query in calls:
            self.assertNotIn("listKeys", " ".join(args))
            self.assertNotIn("regenerate", " ".join(args))
            self.assertNotIn("create", args)
            self.assertIsInstance(query, str)

    def test_reports_do_not_emit_projected_resource_ids_or_unexpected_data(self):
        values = sample()
        values["redis"]["unexpected"] = "synthetic-sensitive-response"
        report = json.dumps(probe.evaluate(SUB, values))
        self.assertNotIn(SUB, report)
        self.assertNotIn(VNET, report)
        self.assertNotIn("synthetic-sensitive-response", report)

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
