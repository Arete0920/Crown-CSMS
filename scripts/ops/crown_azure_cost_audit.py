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
import re
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

COST_API = "2025-03-01"


class ReadUnavailable(Exception):
    """Azure data was not retrievable; never interpret as zero."""

    def __init__(self, reason, category="UNKNOWN"):
        super().__init__(reason)
        self.category = category


ERROR_CATEGORIES = frozenset({
    "ACCESS_DENIED", "AUTHENTICATION", "RATE_LIMIT", "INVALID_REQUEST",
    "PROVIDER_UNAVAILABLE", "CLI_UNAVAILABLE", "TIMEOUT", "INVALID_RESPONSE",
    "UNKNOWN",
})


def error_category(stderr):
    """Return fixed labels only; never retain provider text or identifiers."""
    codes = re.findall(r"\(([A-Za-z][A-Za-z0-9]*)\)", stderr or "")
    # az rest renders HTTP failures as Forbidden({"error":{"code":...}}),
    # unlike other commands' (AuthorizationFailed) format.
    codes += re.findall(r'"code"\s*:\s*"([A-Za-z][A-Za-z0-9]*)"', stderr or "")
    reasons = {"Forbidden": "Forbidden", "Unauthorized": "Unauthorized",
               "Too Many Requests": "TooManyRequests", "Bad Request": "BadRequest",
               "Service Unavailable": "ServiceUnavailable",
               "Internal Server Error": "InternalServerError"}
    for reason, code in reasons.items():
        if re.search(r"(?:^|\n)\s*(?:ERROR:\s*)?" + re.escape(reason) + r"(?:\(|\s*$)", stderr or ""):
            codes.append(code)
    mapping = {
        "AuthorizationFailed": "ACCESS_DENIED", "Forbidden": "ACCESS_DENIED",
        "Unauthorized": "AUTHENTICATION", "AuthenticationFailed": "AUTHENTICATION",
        "InvalidAuthenticationToken": "AUTHENTICATION",
        "ExpiredAuthenticationToken": "AUTHENTICATION",
        "TooManyRequests": "RATE_LIMIT", "BadRequest": "INVALID_REQUEST",
        "InvalidApiVersionParameter": "INVALID_REQUEST",
        "NoRegisteredProviderFound": "INVALID_REQUEST",
        "ServiceUnavailable": "PROVIDER_UNAVAILABLE",
        "InternalServerError": "PROVIDER_UNAVAILABLE",
    }
    return next((mapping[code] for code in codes if code in mapping), "UNKNOWN")


def redacted_diagnostics(report):
    """Export no account IDs, resource names, amounts, or exception messages."""
    allowed = {"cost_MonthToDate", "cost_TheLastMonth", "budgets",
               "group_cost_MonthToDate", "group_cost_TheLastMonth", "group_budgets"}
    statuses = {"COLLECTED", "COLLECTED_NO_ROWS", "UNAVAILABLE"}
    group_costs = report.get("resource_group_cost") or {}
    return {
        "cost_scope": "subscription",
        "resource_group_probe": {
            key: (group_costs.get(key) or {}).get("status")
            if (group_costs.get(key) or {}).get("status") in statuses else "UNAVAILABLE"
            for key in ("month_to_date", "last_month")
        },
        "resource_group_budget_status": "COLLECTED" if report.get("resource_group_budgets") is not None else "UNAVAILABLE",
        "failures": [
            {"section": item["section"], "status": "UNAVAILABLE",
             "category": item.get("category") if item.get("category") in ERROR_CATEGORIES else "UNKNOWN"}
            for item in report.get("failures", []) if item.get("section") in allowed
        ],
        "note": "Missing billing data is unknown, never zero. Error labels are diagnostic hints, not proof of effective permissions.",
    }


def az_json(*parts, timeout=60):
    env = dict(os.environ)
    env["AZURE_EXTENSION_USE_DYNAMIC_INSTALL"] = "no"
    cmd = ["az", *parts, "--output", "json", "--only-show-errors"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=timeout, env=env
        )
    except subprocess.TimeoutExpired as exc:
        raise ReadUnavailable("Azure CLI read timed out", "TIMEOUT") from exc
    except OSError as exc:
        raise ReadUnavailable("Azure CLI is unavailable", "CLI_UNAVAILABLE") from exc
    if result.returncode:
        # Do not expose stderr; it could contain private Azure account details.
        raise ReadUnavailable("Azure read failed", error_category(result.stderr))
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ReadUnavailable("Azure returned invalid JSON", "INVALID_RESPONSE") from exc


def safe_read(label, *parts, failures):
    try:
        return az_json(*parts)
    except ReadUnavailable as exc:
        failures.append({
            "section": label,
            "status": "UNAVAILABLE",
            "reason": str(exc),
            "category": exc.category,
        })
        return None


def billing(scope, timeframe, failures, label_prefix="cost_"):
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
        label_prefix + timeframe, "rest", "--method", "post", "--url", url,
        "--body", json.dumps(query), failures=failures
    )
    if not isinstance(result, dict):
        return {"status": "UNAVAILABLE", "note": "Unknown, not $0."}
    properties = result.get("properties") or {}
    columns = [col.get("name", "") for col in properties.get("columns") or []]
    rows = properties.get("rows")
    if not columns or not isinstance(rows, list):
        failures.append({
            "section": label_prefix + timeframe,
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
    # Cost Management can paginate. Never describe the first page as complete.
    # Preserve the observed rows for private diagnosis, but make partial totals
    # unusable as evidence of actual spending or budget compliance.
    partial = bool(properties.get("nextLink"))
    if partial:
        failures.append({
            "section": label_prefix + timeframe,
            "status": "UNAVAILABLE",
            "reason": "Cost Management result has additional uncollected pages",
            "category": "INVALID_RESPONSE",
        })
    return {
        "status": "UNAVAILABLE" if partial else ("COLLECTED" if rows else "COLLECTED_NO_ROWS"),
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
    # Probe the already-authorized group separately. Never present its costs
    # as the subscription total or silently replace unavailable billing data.
    group_scope = scope + "/resourceGroups/" + quote(group, safe="")
    group_costs = {
        "month_to_date": billing(group_scope, "MonthToDate", failures, "group_cost_"),
        "last_month": billing(group_scope, "TheLastMonth", failures, "group_cost_"),
    }
    group_budget_raw = safe_read(
        "group_budgets", "rest", "--method", "get", "--url",
        "https://management.azure.com" + group_scope
        + "/providers/Microsoft.Consumption/budgets?api-version=2023-05-01",
        failures=failures,
    )
    group_budgets = None
    if isinstance(group_budget_raw, dict) and isinstance(group_budget_raw.get("value"), list):
        group_budgets = group_budget_raw["value"]
    elif group_budget_raw is not None:
        failures.append({"section": "group_budgets", "status": "UNAVAILABLE",
                         "category": "INVALID_RESPONSE", "reason": "Budget list response was not usable"})
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
        "resource_group_cost": group_costs,
        "resource_group_budgets": group_budgets,
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

