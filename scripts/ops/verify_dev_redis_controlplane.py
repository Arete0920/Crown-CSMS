#!/usr/bin/env python3
"""Read-only Azure DEV Redis control-plane inventory, issue #427.

No secrets are fetched, no raw Azure responses are emitted, and no resources
are modified. Control-plane agreement is not hosted release certification.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

GROUP = "crown-rg"
APP = "crown-api-dev"
CACHE = "crown-auth-cache-dev"
ENDPOINT = "pe-crown-auth-cache-dev"
ZONE = "privatelink.redis.azure.net"
UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
CACHE_KEYS = {"CROWN_CACHE_URL"}

READS = (
    ("redis", ("redisenterprise", "show", "-g", GROUP, "-n", CACHE),
     "{state:provisioningState,public:publicNetworkAccess,tls:minimumTlsVersion,sku:sku.name,location:location}"),
    ("redis_database", ("redisenterprise", "database", "show", "-g", GROUP, "--cluster-name", CACHE),
     "{state:provisioningState,client:clientProtocol,clustering:clusteringPolicy,eviction:evictionPolicy,port:port}"),
    ("private_endpoint", ("network", "private-endpoint", "show", "-g", GROUP, "-n", ENDPOINT),
     "{state:provisioningState,subnet:subnet.id,connections:privateLinkServiceConnections[].{target:privateLinkServiceId,status:privateLinkServiceConnectionState.status,groups:groupIds}}"),
    ("dns_zone_groups", ("network", "private-endpoint", "dns-zone-group", "list", "-g", GROUP, "--endpoint-name", ENDPOINT),
     "[].{state:provisioningState,zones:privateDnsZoneConfigs[].privateDnsZoneId}"),
    ("dns_vnet_links", ("network", "private-dns", "link", "vnet", "list", "-g", GROUP, "-z", ZONE),
     "[].{state:provisioningState,vnet:virtualNetwork.id}"),
    ("dns_a_records", ("network", "private-dns", "record-set", "a", "list", "-g", GROUP, "-z", ZONE),
     "[].{name:name,count:length(aRecords)}"),
    ("app_vnet", ("webapp", "vnet-integration", "list", "-g", GROUP, "-n", APP),
     "[].{subnet:subnetResourceId,vnet:vnetResourceId}"),
    ("app_setting_names", ("webapp", "config", "appsettings", "list", "-g", GROUP, "-n", APP),
     "[].name"),
)


def azure_read(args, query, *, subscription=None, runner=subprocess.run):
    """Require projected JSON; suppress CLI errors and output entirely on failure."""
    command = ["az", *args]
    if subscription:
        command.extend(["--subscription", subscription])
    command.extend(["--query", query, "--output", "json", "--only-show-errors"])
    try:
        response = runner(command, capture_output=True, text=True, timeout=30, check=False)
        if response.returncode or len(response.stdout) > 30000:
            return None
        return json.loads(response.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
        return None


def same_id(actual, expected):
    return isinstance(actual, str) and actual.casefold() == expected.casefold()


def subnet_vnet(value):
    if not isinstance(value, str) or value.lower().count("/subnets/") != 1:
        return None
    return re.split("/subnets/", value, flags=re.IGNORECASE)[0]


def evaluate(subscription, readings):
    """Return only bounded classifications, never raw resource IDs or settings."""
    checks = {key: "NOT_VERIFIED" for key, _, _ in READS}
    redis = readings.get("redis")
    if isinstance(redis, dict):
        checks["redis"] = "CONSISTENT" if (
            redis.get("state") == "Succeeded"
            and redis.get("public") == "Disabled"
            and str(redis.get("tls")) == "1.2"
            and redis.get("sku") == "Balanced_B0"
            and redis.get("location") == "eastus"
        ) else "BLOCKED"

    database = readings.get("redis_database")
    if isinstance(database, dict):
        checks["redis_database"] = "CONSISTENT" if (
            database.get("state") == "Succeeded"
            and database.get("client") == "Encrypted"
            and database.get("clustering") == "NoCluster"
            and database.get("eviction") == "NoEviction"
            and database.get("port") == 10000
        ) else "BLOCKED"

    endpoint = readings.get("private_endpoint")
    vnet = subnet_vnet(endpoint.get("subnet")) if isinstance(endpoint, dict) else None
    cache_id = (f"/subscriptions/{subscription}/resourceGroups/{GROUP}"
                f"/providers/Microsoft.Cache/redisEnterprise/{CACHE}")
    if isinstance(endpoint, dict):
        links = endpoint.get("connections")
        checks["private_endpoint"] = "CONSISTENT" if (
            endpoint.get("state") == "Succeeded" and vnet
            and isinstance(links, list)
            and any(isinstance(link, dict)
                    and same_id(link.get("target"), cache_id)
                    and link.get("status") == "Approved"
                    and isinstance(link.get("groups"), list)
                    and "redisEnterprise" in link["groups"] for link in links)
        ) else "BLOCKED"

    zone_id = (f"/subscriptions/{subscription}/resourceGroups/{GROUP}"
               f"/providers/Microsoft.Network/privateDnsZones/{ZONE}")
    zones = readings.get("dns_zone_groups")
    if isinstance(zones, list):
        checks["dns_zone_groups"] = "CONSISTENT" if any(
            isinstance(zone, dict) and zone.get("state") == "Succeeded"
            and isinstance(zone.get("zones"), list)
            and any(same_id(x, zone_id) for x in zone["zones"])
            for zone in zones
        ) else "BLOCKED"

    links = readings.get("dns_vnet_links")
    if isinstance(links, list):
        checks["dns_vnet_links"] = "CONSISTENT" if vnet and any(
            isinstance(link, dict) and link.get("state") == "Succeeded"
            and same_id(link.get("vnet"), vnet) for link in links
        ) else "BLOCKED"

    records = readings.get("dns_a_records")
    if isinstance(records, list):
        checks["dns_a_records"] = "CONSISTENT" if any(
            isinstance(record, dict)
            and record.get("name") == f"{CACHE}.eastus"
            and isinstance(record.get("count"), int)
            and not isinstance(record.get("count"), bool)
            and record["count"] > 0 for record in records
        ) else "BLOCKED"

    app_links = readings.get("app_vnet")
    if isinstance(app_links, list):
        checks["app_vnet"] = "CONSISTENT" if vnet and any(
            isinstance(link, dict) and (
                same_id(subnet_vnet(link.get("subnet")), vnet)
                or same_id(link.get("vnet"), vnet)
            ) for link in app_links
        ) else "BLOCKED"

    names = readings.get("app_setting_names")
    if isinstance(names, list) and all(isinstance(name, str) for name in names):
        checks["app_setting_names"] = "PRESENT_ONLY" if CACHE_KEYS.intersection(names) else "BLOCKED"

    consistent = all(status in {"CONSISTENT", "PRESENT_ONLY"} for status in checks.values())
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": "crown-rg/crown-api-dev + crown-auth-cache-dev",
        "subscription_match": True,
        "checks": checks,
        "control_plane_metadata": "CONSISTENT" if consistent else "BLOCKED",
        "hosted_redis_connectivity": "NOT_TESTED",
        "effective_secret_or_key_vault_resolution": "NOT_VERIFIED",
        "private_dns_resolution_from_app": "NOT_TESTED",
        "cross_worker_429_and_unavailable_503": "NOT_TESTED",
        "deployed_source_sha_and_rollback": "NOT_VERIFIED",
        "release_certification": "NOT_VERIFIED",
        "limitations": [
            "Control-plane projections do not prove effective process settings.",
            "Setting names do not verify resolved Key Vault references or TLS credentials.",
            "Private DNS metadata does not prove resolution from the App Service subnet.",
            "No credentials, network probes, tenant actions, or Azure writes were performed.",
        ],
    }


def collect(expected_subscription, *, read=azure_read):
    if not isinstance(expected_subscription, str) or not UUID.fullmatch(expected_subscription):
        return {"preflight": "BLOCKED", "reason": "EXPECTED_SUBSCRIPTION_NOT_PINNED",
                "release_certification": "NOT_VERIFIED"}
    selected = read(("account", "show"), "id")
    if not same_id(selected, expected_subscription):
        return {"preflight": "BLOCKED", "reason": "AZURE_SUBSCRIPTION_MISMATCH_OR_UNAVAILABLE",
                "release_certification": "NOT_VERIFIED"}
    readings = {name: read(args, query, subscription=expected_subscription)
                for name, args, query in READS}
    result = evaluate(expected_subscription, readings)
    result["preflight"] = result["control_plane_metadata"]
    return result


def main():
    expected = os.getenv("CROWN_EXPECTED_AZURE_SUBSCRIPTION_ID", "").strip()
    report = collect(expected)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report.get("control_plane_metadata") == "CONSISTENT" else 2


if __name__ == "__main__":
    sys.exit(main())
