#!/usr/bin/env python3
"""Read-only Azure cost/resource inventory for CROWN.

Run from an authenticated Azure Cloud Shell session. Keep output PRIVATE:
subscription identifiers, resource inventory, and costs are sensitive.
No create/update/delete/stop/start commands are issued.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

COST_API = "2025-03-01"


class ReadUnavailable(Exception):
    """Azure data was not retrievable; never interpret as zero."""


def az_json(*parts, timeout=60):
    env = dict(os.environ)
    env["AZURE_EXTENSION_USE_DYNAMIC_INSTALL"] = "no"
    cmd = ["az", *parts, "--output", "json", "--only-show-errors"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=timeout, env=env
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReadUnavailable("Azure CLI is unavailable or timed out") from exc
    if result.returncode:
        # Do not expose stderr; it could contain private Azure account details.
        raise ReadUnavailable("Azure read failed or permissions were insufficient")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ReadUnavailable("Azure returned invalid JSON") from exc


def safe_read(label, *parts, failures):
    try:
        return az_json(*parts)
    except ReadUnavailable as exc:
        failures.append({
            "section": label,
            "status": "UNAVAILABLE",
            "reason": str(exc)
        })
        return None


def billing(scope, timeframe, failures):
    """Read-only Azure Cost Management query (REST uses POST for queries)."""
    url = (
        "https://management.azure.com" + scope
        + "/providers/Microsoft.CostManagement/query?api-version=" + COST_API
    )
    query = {
        "type": "ActualCost",
        "timeframe": timeframe,
        "dataset": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {"name": "PreTaxCost", "function": "Sum"}
            },
            "grouping": [{"type": "Dimension", "name": "ResourceGroup"}],
        },
    }
    result = safe_read(
        "cost_" + timeframe, "rest", "--method", "post", "--url", url,
        "--body", json.dumps(query), failures=failures
    )
    if not isinstance(result, dict):
        return {"status": "UNAVAILABLE", "note": "Unknown, not $0."}
    properties = result.get("properties") or {}
    columns = [col.get("name", "") for col in properties.get("columns") or []]
    rows = properties.get("rows")
    if not columns or not isinstance(rows, list):
        failures.append({
            "section": "cost_" + timeframe,
            "status": "UNAVAILABLE",
            "reason": "Cost query response had no usable columns or rows",
        })
        return {"status": "UNAVAILABLE", "note": "Unknown, not $0."}
    extracted = []
    for row in rows:
        data = dict(zip(columns, row))
        extracted.append({
            "resource_group": data.get(
                "ResourceGroup", data.get("ResourceGroupName", "")
            ),
            "amount": data.get("Cost", data.get("PreTaxCost")),
            "currency": data.get("Currency", ""),
        })
    return {
        "status": "COLLECTED" if rows else "COLLECTED_NO_ROWS",
        "timeframe": timeframe,
        "grouped_by": "ResourceGroup",
        "rows": extracted,
        "has_more_pages": bool(properties.get("nextLink")),
        "note": (
            "Billing data can lag. An empty result is not proof of $0. "
            "This query might exclude taxes, support, or other charges."
        ),
    }


def make_report(group):
    failures = []
    account = safe_read(
        "account", "account", "show", "--query",
        "{id:id,name:name,state:state}", failures=failures
    )
    if (
        not isinstance(account, dict)
        or not account.get("id")
        or account.get("state") != "Enabled"
    ):
        return {
            "status": "BLOCKED",
            "reason": "No verified enabled Azure subscription selected.",
            "failures": failures,
        }
    subscription = account["id"]
    args = ["--subscription", subscription, "--resource-group", group]
    inventory_queries = {
        "resources": (
            "resource", "list", *args, "--query",
            "[].{name:name,type:type,location:location}"
        ),
        "app_service_plans": (
            "appservice", "plan", "list", *args, "--query",
            "[].{name:name,tier:sku.tier,sku:sku.name,instances:sku.capacity}"
        ),
        "webapps": (
            "webapp", "list", *args, "--query",
            "[].{name:name,state:state,kind:kind,plan:serverFarmId}"
        ),
        "container_registries": (
            "acr", "list", *args, "--query",
            "[].{name:name,sku:sku.name,admin_enabled:adminUserEnabled}"
        ),
        "static_web_apps": (
            "staticwebapp", "list", *args, "--query",
            "[].{name:name,sku:sku.name}"
        ),
        "postgresql_flexible_servers": (
            "postgres", "flexible-server", "list", *args, "--query",
            "[].{name:name,sku:sku.name,tier:sku.tier,state:state}"
        ),
        "storage_accounts": (
            "storage", "account", "list", *args, "--query",
            "[].{name:name,sku:sku.name,kind:kind}"
        ),
        "container_apps": (
            "containerapp", "list", *args, "--query",
            "[].{name:name}"
        ),
    }
    inventory = {
        name: safe_read(name, *cmd, failures=failures)
        for name, cmd in inventory_queries.items()
    }
    scope = "/subscriptions/" + subscription
    costs = {
        "month_to_date": billing(scope, "MonthToDate", failures),
        "last_month": billing(scope, "TheLastMonth", failures),
    }
    budget_url = (
        "https://management.azure.com" + scope
        + "/providers/Microsoft.Consumption/budgets?api-version=2023-05-01"
    )
    raw_budgets = safe_read(
        "budgets", "rest", "--method", "get", "--url", budget_url,
        failures=failures
    )
    budgets = None
    if isinstance(raw_budgets, dict) and isinstance(raw_budgets.get("value"), list):
        budgets = [
            {
                "name": item.get("name"),
                "amount": (item.get("properties") or {}).get("amount"),
                "time_grain": (item.get("properties") or {}).get("timeGrain"),
            }
            for item in raw_budgets["value"]
        ]
    elif raw_budgets is not None:
        failures.append({
            "section": "budgets",
            "status": "UNAVAILABLE",
            "reason": "Budget list response was not usable",
        })
    return {
        "status": (
            "COLLECTED_WITH_GAPS" if failures
            else "READ_ONLY_INVENTORY_COLLECTED"
        ),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "subscription": {"name": account.get("name"), "id": subscription},
        "resource_group": group,
        "inventory": inventory,
        "actual_cost": costs,
        "existing_budgets": budgets,
        "failures": failures,
        "notes": [
            "Read-only: no resources or budgets were altered.",
            "Keep this report private; do not upload it to the public repository.",
            "Missing data means UNKNOWN, never $0.",
            "Pay-As-You-Go budget notifications do not cap spending.",
            "Resources outside the selected group can still incur charges.",
            "This audit does not certify production or deployment health.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-group", default="crown-rg")
    parser.add_argument("--output", help="Private local JSON output path")
    args = parser.parse_args(argv)
    report = make_report(args.resource_group)
    data = json.dumps(report, indent=2) + "\n"
    if args.output:
        path = Path(args.output).expanduser()
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError:
            print("Output exists or cannot be created. No report overwritten.", file=sys.stderr)
            return 2
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
        print("Private local Azure cost report written. Do not commit to GitHub.")
    else:
        print(data)
    return 2 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
