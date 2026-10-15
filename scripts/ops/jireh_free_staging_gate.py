#!/usr/bin/env python3
"""Fail-closed, read-only admission and postcondition checks for isolated Jireh SWA Free."""
import argparse
import json
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$")
MAX_FREE_SITES = 10

class AdmissionDenied(Exception):
    pass

def check_name(name):
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise AdmissionDenied("Invalid Azure name")
    return name

def tier(resource):
    if not isinstance(resource, dict):
        raise AdmissionDenied("Malformed Azure record")
    sku = resource.get("sku")
    if isinstance(sku, dict):
        sku = sku.get("name")
    if not isinstance(sku, str) or sku.lower() not in ("free", "standard", "dedicated"):
        raise AdmissionDenied("Unknown or unavailable SKU")
    return sku.lower()

def ownership(resource):
    rid = resource.get("id")
    if not isinstance(rid, str):
        raise AdmissionDenied("Missing Azure resource ID")
    match = re.search(r"/resourceGroups/([^/]+)/providers/Microsoft\.Web/staticSites/([^/]+)$", rid, re.I)
    if not match:
        raise AdmissionDenied("Unexpected Azure resource ownership ID")
    return match.group(1), match.group(2)

def plan(resources, name="jireh-site", group="crown-rg"):
    check_name(name)
    check_name(group)
    if not isinstance(resources, list) or len(resources) > 500:
        raise AdmissionDenied("Subscription inventory cannot be trusted")
    found = []
    free_count = 0
    for r in resources:
        if tier(r) == "free":
            free_count += 1
        owner_group, owner_name = ownership(r)
        if owner_name.lower() == name.lower():
            found.append((r, owner_group))
    if len(found) > 1:
        raise AdmissionDenied("Duplicate Jireh site identity")
    if found:
        resource, owner_group = found[0]
        if owner_group.lower() != group.lower() or tier(resource) != "free":
            raise AdmissionDenied("Jireh site belongs to another owner or paid tier")
        return "REUSE_VERIFIED_FREE"
    if free_count >= MAX_FREE_SITES:
        raise AdmissionDenied("No free-tier quota remains")
    return "CREATE_FREE"

def verify(resource, name="jireh-site", group="crown-rg"):
    check_name(name)
    check_name(group)
    owner_group, owner_name = ownership(resource)
    if tier(resource) != "free" or owner_group.lower() != group.lower() or owner_name.lower() != name.lower():
        raise AdmissionDenied("Post-provision resource is not isolated and free")
    return True

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--inventory")
    g.add_argument("--verify-resource")
    parser.add_argument("--name", default="jireh-site")
    parser.add_argument("--group", default="crown-rg")
    args = parser.parse_args()
    try:
        obj = json.loads(Path(args.inventory or args.verify_resource).read_text())
        if args.inventory:
            print(plan(obj, args.name, args.group))
        else:
            verify(obj, args.name, args.group)
            print("VERIFIED_FREE")
    except (AdmissionDenied, ValueError, OSError):
        raise SystemExit("BLOCKED: Azure Static Web Apps Free entitlement cannot be confirmed") from None

if __name__ == "__main__":
    main()
