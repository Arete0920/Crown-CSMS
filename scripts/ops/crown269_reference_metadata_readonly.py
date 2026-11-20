#!/usr/bin/env python3
"""#269: inspect two specific App Service Key Vault references without exposing values.

Uses Azure CLI authenticated by the existing Azure DEV OIDC GitHub environment.
Read-only: one az account show and exactly two fixed Microsoft.Web ARM GETs.
Never requests app-setting values, Key Vault secret values, raw reference strings,
versions, credentials, logs, or Azure resource mutations.
"""

import datetime as datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# Previously established DEV resource identity; do not expand scope.
SUBSCRIPTION_ID = "4ef0ba4b-4810-48d4-b3fe-953a9708953a"
RESOURCE_GROUP = "crown-rg"
WEB_APP = "crown-api-dev"
KEY_VAULT = "crown-kv-prod"
API_VERSION = "2025-05-01"
TARGETS = {
    "CROWN_OPS_SECRET": "crown-dev-crown-ops-secret",
    "DEV_OPS_SECRET": "crown-dev-dev-ops-secret",
}
ALLOWED_RESOLVE_STATUSES = frozenset({
    "Initialized", "Resolved", "InvalidSyntax", "MSINotEnabled", "VaultNotFound",
    "SecretNotFound", "SecretVersionNotFound", "AccessToKeyVaultDenied",
    "OtherReasons", "FetchTimedOut", "UnauthorizedClient",
})
SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")
RUN_PATTERN = re.compile(r"^[1-9][0-9]{0,19}$")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def api_url(setting):
    if setting not in TARGETS:
        raise ValueError("NOT_IN_FIXED_TARGET_ALLOWLIST")
    return (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Web/sites/{WEB_APP}"
        f"/config/configreferences/appsettings/{setting}?api-version={API_VERSION}"
    )


def metadata_projection(setting):
    """JMESPath runs inside az; full ARM object is never sent to stdout."""
    if setting not in TARGETS:
        raise ValueError("NOT_IN_FIXED_TARGET_ALLOWLIST")
    return (
        "{status:properties.status,"
        "source_ok:properties.source=='KeyVault',"
        f"target_ok:properties.vaultName=='{KEY_VAULT}' && "
        f"properties.secretName=='{TARGETS[setting]}',"
        "active_version_present:properties.activeVersion!=`null` && "
        "properties.activeVersion!=''}"
    )


def read_az(args):
    """Suppress stderr and raw stdout even on failure; return dict or None."""
    try:
        result = subprocess.run(
            ["az", *args, "--output", "json", "--only-show-errors"],
            capture_output=True, text=True, encoding="utf-8", check=False,
            timeout=40, shell=False,
        )
        if result.returncode != 0:
            return None
        value = json.loads(result.stdout)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        return None


def safe_context(environment):
    sha = environment.get("GITHUB_SHA", "").lower()
    run = environment.get("GITHUB_RUN_ID", "")
    return {
        "github_source_sha": sha if SHA_PATTERN.fullmatch(sha) else "NOT_VERIFIED",
        "github_run_id": run if RUN_PATTERN.fullmatch(run) else "NOT_VERIFIED",
    }


def inspect(environment=None, reader=read_az):
    environment = os.environ if environment is None else environment
    response = {
        "issue": "269",
        "purpose": "DEV App Service two-reference Key Vault metadata-only read",
        "started_utc": now(),
        "mode": "ARM_GET_ONLY_NO_SECRET_VALUES_OR_HASHES",
        "subscription": SUBSCRIPTION_ID,
        "resource_group": RESOURCE_GROUP,
        "app": WEB_APP,
        **safe_context(environment),
        "oidc_tenant_match": False,
        "subscription_match": False,
        "overall": "NOT_VERIFIED",
        "checks": [],
        "legacy_ops_secret_presence": "NOT_VERIFIED_AVOIDS_APPSETTING_VALUE_READ",
        "historical_credential_dev_ops_applicability": "NOT_PROVEN",
        "historical_copy_custody": "NOT_VERIFIED",
        "limitations": [
            "Reference metadata cannot prove actual credential values, equality or historical denial.",
            "The fixed per-setting reference API cannot prove absence of a literal OPS_SECRET setting.",
            "No Windows, OneDrive, source-history, or external-consumer credential-copy inspection.",
            "A successful OIDC login does not establish permission to call the ARM reference GET.",
        ],
        "azure_resource_mutations": "NONE",
        "github_resource_mutations": "NONE_BY_THIS_CHECKER",
        "secret_values_or_hashes_emitted": False,
    }
    # This expected tenant comes from the exact existing dev-environment OIDC login
    # configuration. It is never copied into the emitted receipt.
    expected_tenant = environment.get("CROWN269_EXPECTED_TENANT", "")
    expected_subscription = environment.get("CROWN269_EXPECTED_SUBSCRIPTION", "")
    if (not re.fullmatch(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", expected_tenant)
            or expected_subscription.lower() != SUBSCRIPTION_ID):
        response["overall"] = "BLOCKED_EXPECTED_OIDC_IDENTITY_NOT_CONFIGURED"
        response["finished_utc"] = now()
        return response
    account = reader(["account", "show", "--query", "{id:id,tenant:tenantId}"])
    if account is None:
        response["overall"] = "BLOCKED_AZURE_CLI_AUTH_OR_ACCOUNT_READ"
        response["finished_utc"] = now()
        return response
    response["subscription_match"] = (
        isinstance(account.get("id"), str)
        and account["id"].lower() == SUBSCRIPTION_ID
    )
    response["oidc_tenant_match"] = (
        isinstance(account.get("tenant"), str)
        and account["tenant"].lower() == expected_tenant.lower()
    )
    if not (response["subscription_match"] and response["oidc_tenant_match"]):
        response["overall"] = "BLOCKED_WRONG_AZURE_ACCOUNT_OR_TENANT"
        response["finished_utc"] = now()
        return response
    for key in TARGETS:
        projected = reader([
            "rest", "--method", "GET", "--url", api_url(key),
            "--query", metadata_projection(key),
        ])
        check = {"setting": key, "outcome": "NOT_VERIFIED_ARM_READ_UNAVAILABLE"}
        if projected is not None:
            raw_status = projected.get("status")
            status = (raw_status if isinstance(raw_status, str) and
                      raw_status in ALLOWED_RESOLVE_STATUSES else "UNRECOGNIZED")
            check.update({
                "status": status,
                "status_resolved": status == "Resolved",
                "source_keyvault": projected.get("source_ok") is True,
                "expected_target_match": projected.get("target_ok") is True,
                "active_version_present": projected.get("active_version_present") is True,
            })
            check["outcome"] = (
                "RESOLVED_CORRECT_TARGET_AND_VERSION_METADATA_ONLY"
                if all((check["status_resolved"], check["source_keyvault"],
                        check["expected_target_match"], check["active_version_present"]))
                else "REVIEW_REQUIRED_REFERENCE_NOT_FULLY_VERIFIED"
            )
        response["checks"].append(check)
    response["overall"] = (
        "PASS_TWO_REFERENCE_METADATA_ONLY_OTHER_269_ITEMS_OPEN"
        if all(v["outcome"] == "RESOLVED_CORRECT_TARGET_AND_VERSION_METADATA_ONLY"
               for v in response["checks"])
        else "REVIEW_REQUIRED_KEYVAULT_REFERENCE_METADATA"
    )
    response["finished_utc"] = now()
    return response


def checked_receipt_path(value):
    """Permit only the existing private Actions runner metadata receipt."""
    runner_temp = os.environ.get("RUNNER_TEMP", "")
    root = Path(runner_temp)
    path = Path(value)
    try:
        if (
            not runner_temp or not root.is_absolute() or not root.is_dir()
            or root.is_symlink() or not path.is_absolute()
            or path != root / "crown269-dev-reference-metadata.json"
            or path.is_symlink()
            or path.parent.resolve(strict=True) != root.resolve(strict=True)
            or path.exists()
        ):
            raise ValueError("unsafe receipt path")
    except (OSError, RuntimeError) as exc:
        raise ValueError("unsafe receipt path") from exc
    return path


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] != "--receipt":
        print("USAGE: --receipt NEW_LOCAL_JSON_PATH", file=sys.stderr)
        return 2
    try:
        receipt = checked_receipt_path(args[1])
    except (OSError, ValueError):
        print("BLOCKED_LOCAL_RECEIPT_PATH_INVALID", file=sys.stderr)
        return 3
    outcome = inspect()
    serialized = json.dumps(outcome, sort_keys=True, indent=2) + "\n"
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(receipt, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(serialized)
    except OSError:
        print("BLOCKED_LOCAL_RECEIPT_NOT_CREATED_OR_ALREADY_EXISTS", file=sys.stderr)
        return 3
    # Only whitelisted receipt fields can reach logs, not Azure raw metadata.
    print(serialized, end="")
    return 0 if outcome["overall"].startswith("PASS_TWO_REFERENCE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
