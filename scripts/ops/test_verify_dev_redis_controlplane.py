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
CACHE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Cache/Redis/crown-auth-cache-dev"
ZONE = f"/subscriptions/{SUB}/resourceGroups/crown-rg/providers/Microsoft.Network/privateDnsZones/privatelink.redis.azure.net"

def sample():
    return {
        "redis": dict(state="Succeeded", public="Disabled", tls="1.2", nonTls=False, sku="Basic", family="C", capacity=0, eviction="noeviction"),
        "private_endpoint": dict(state="Succeeded", subnet=VNET + "/subnets/private", connections=[dict(target=CACHE, status="Approved")]),
        "dns_zone_groups": [dict(state="Succeeded", zones=[ZONE])],
        "dns_vnet_links": [dict(state="Succeeded", vnet=VNET)],
        "dns_a_records": 1,
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
            ("private_endpoint", dict(state="Succeeded", subnet=VNET+"/subnets/private", connections=[])),
            ("dns_zone_groups", []), ("dns_vnet_links", []), ("dns_a_records", 0),
            ("app_vnet", []), ("app_setting_names", []),
        ]:
            with self.subTest(name=name):
                values = sample()
                values[name] = replacement
                self.assertEqual(probe.evaluate(SUB, values)["control_plane_metadata"], "BLOCKED")

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
        self.assertIsNone(probe.azure_read(("redis", "show"), "sku.name", subscription=SUB, runner=bad))

if __name__ == "__main__":
    unittest.main()
