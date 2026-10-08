#!/usr/bin/env python3
"""Fail closed on unregistered or weakly governed external tool integrations."""
from __future__ import annotations

import ipaddress
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config" / "security" / "external_tool_integrations.json"
POLICY = ROOT / "docs" / "security" / "EXTERNAL_TOOL_INTEGRATION_SECURITY_STANDARD.md"

REQUIRED_DEFAULTS = {
    "default_access": "deny",
    "default_tool_mode": "read_only",
    "registered_only": True,
    "require_tenant_reauthorization": True,
    "require_scoped_credentials": True,
    "require_namespaced_tools": True,
    "require_pinned_version": True,
    "require_artifact_digest": True,
    "require_egress_allowlist": True,
    "require_durable_audit": True,
    "require_human_approval_for_writes": True,
    "untrusted_content_can_authorize_tools": False,
    "fail_closed": True,
}

ALLOWED_STATUS = {"approved", "disabled"}
ALLOWED_TRANSPORT = {"local", "remote", "gateway", "embedded"}
ALLOWED_DATA = {
    "public",
    "internal",
    "school-confidential",
    "student-education-record",
    "health",
    "financial",
    "credential",
}
WRITE_MARKERS = (".write", ".send", ".modify", ".delete", ".execute", ".refund", ".disburse")
PROTECTED_DATA = {
    "school-confidential",
    "student-education-record",
    "health",
    "financial",
    "credential",
}
CONFIG_NAMES = {".mcp.json", "mcp.json", "mcp.yml", "mcp.yaml", "mcp.toml"}
SDK_DEPENDENCIES = {"@modelcontextprotocol/sdk", "modelcontextprotocol", "mcp"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TOOL_RE = re.compile(r"^crown(?:\.[a-z0-9][a-z0-9_-]*)+\.v[1-9][0-9]*$")
VERSION_BAD_RE = re.compile(r"(^|[<>=~^*xX ])latest($|[ ,])|[*xX]")


class PolicyError(RuntimeError):
    pass


def _tracked_files() -> list[Path]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [ROOT / p for p in proc.stdout.decode("utf-8").split("\0") if p]


def _load_registry() -> dict:
    if not POLICY.is_file():
        raise PolicyError(f"missing policy document: {POLICY.relative_to(ROOT)}")
    if not REGISTRY.is_file():
        raise PolicyError(f"missing registry: {REGISTRY.relative_to(ROOT)}")
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid registry JSON: {exc}") from exc
    if data.get("schema_version") != 1:
        raise PolicyError("registry schema_version must be 1")
    if data.get("policy") != str(POLICY.relative_to(ROOT)).replace("\\", "/"):
        raise PolicyError("registry policy pointer does not match canonical policy path")
    defaults = data.get("defaults")
    if not isinstance(defaults, dict):
        raise PolicyError("registry defaults must be an object")
    for key, expected in REQUIRED_DEFAULTS.items():
        if defaults.get(key) != expected:
            raise PolicyError(f"registry default {key!r} must be {expected!r}")
    integrations = data.get("integrations")
    if not isinstance(integrations, list):
        raise PolicyError("registry integrations must be a list")
    return data


def _validate_hostname(host: str) -> bool:
    if not host or "://" in host or "/" in host or "*" in host:
        return False
    normalized = host.lower().rstrip(".")
    parsed = urlparse(f"https://{normalized}")
    if not parsed.hostname or parsed.hostname != normalized:
        return False
    if normalized == "localhost" or normalized.endswith(".localhost") or normalized.endswith(".local"):
        return False
    if normalized in {"metadata.google.internal", "metadata.azure.internal"}:
        return False
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _valid_repo_relative_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def _validate_entry(entry: dict, seen_ids: set[str], seen_tools: set[str]) -> list[str]:
    errors: list[str] = []
    required = {
        "id", "status", "owner", "transport", "version", "artifact_digest",
        "tools", "permissions", "data_classifications", "egress_hosts",
        "config_paths", "human_approval_for_writes", "auto_run",
        "reviewed_at", "disable_procedure",
    }
    missing = sorted(required.difference(entry))
    if missing:
        return [f"registry entry missing fields: {', '.join(missing)}"]

    integration_id = entry.get("id")
    if not isinstance(integration_id, str) or not re.fullmatch(r"crown\.[a-z0-9][a-z0-9_.-]*", integration_id):
        errors.append(f"invalid integration id: {integration_id!r}")
    elif integration_id in seen_ids:
        errors.append(f"duplicate integration id: {integration_id}")
    else:
        seen_ids.add(integration_id)

    if entry.get("status") not in ALLOWED_STATUS:
        errors.append(f"{integration_id}: status must be one of {sorted(ALLOWED_STATUS)}")
    if entry.get("transport") not in ALLOWED_TRANSPORT:
        errors.append(f"{integration_id}: invalid transport")
    if not isinstance(entry.get("owner"), str) or not entry["owner"].strip():
        errors.append(f"{integration_id}: owner is required")

    version = entry.get("version")
    if not isinstance(version, str) or not version.strip() or VERSION_BAD_RE.search(version):
        errors.append(f"{integration_id}: version must be exact and cannot use latest/wildcards")
    digest = entry.get("artifact_digest")
    if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
        errors.append(f"{integration_id}: artifact_digest must be sha256:<64 lowercase hex>")

    tools = entry.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append(f"{integration_id}: at least one namespaced tool is required")
        tools = []
    for tool in tools:
        if not isinstance(tool, str) or not TOOL_RE.fullmatch(tool):
            errors.append(f"{integration_id}: invalid tool namespace {tool!r}")
        elif tool in seen_tools:
            errors.append(f"duplicate tool identity across integrations: {tool}")
        else:
            seen_tools.add(tool)

    permissions = entry.get("permissions")
    if not isinstance(permissions, list) or not permissions or not all(isinstance(p, str) and p for p in permissions):
        errors.append(f"{integration_id}: permissions must be a non-empty string list")
        permissions = []

    data = entry.get("data_classifications")
    if (
        not isinstance(data, list)
        or not data
        or any(item not in ALLOWED_DATA for item in data)
    ):
        errors.append(f"{integration_id}: data_classifications must be a non-empty approved list")
        data = []

    hosts = entry.get("egress_hosts")
    if not isinstance(hosts, list) or any(not isinstance(h, str) or not _validate_hostname(h) for h in hosts):
        errors.append(f"{integration_id}: egress_hosts must contain exact hostnames only")
    if entry.get("transport") in {"remote", "gateway"} and not hosts:
        errors.append(f"{integration_id}: remote/gateway transport requires explicit egress_hosts")

    paths = entry.get("config_paths")
    if (
        not isinstance(paths, list)
        or not paths
        or not all(isinstance(p, str) and _valid_repo_relative_path(p) for p in paths)
    ):
        errors.append(f"{integration_id}: config_paths must be non-empty normalized repository-relative paths")

    writes = any(any(marker in permission for marker in WRITE_MARKERS) for permission in permissions)
    if writes and entry.get("human_approval_for_writes") is not True:
        errors.append(f"{integration_id}: write-capable permission requires human approval")
    if writes and entry.get("auto_run") is not False:
        errors.append(f"{integration_id}: write-capable permission cannot auto-run")
    if any(item in PROTECTED_DATA for item in data) and entry.get("auto_run") is not False:
        errors.append(f"{integration_id}: protected-data tools cannot auto-run")
    if not isinstance(entry.get("human_approval_for_writes"), bool):
        errors.append(f"{integration_id}: human_approval_for_writes must be boolean")
    if not isinstance(entry.get("auto_run"), bool):
        errors.append(f"{integration_id}: auto_run must be boolean")

    reviewed_at = entry.get("reviewed_at")
    try:
        parsed_review_date = date.fromisoformat(reviewed_at) if isinstance(reviewed_at, str) else None
    except ValueError:
        parsed_review_date = None
    if parsed_review_date is None or parsed_review_date.isoformat() != reviewed_at:
        errors.append(f"{integration_id}: reviewed_at must be a valid YYYY-MM-DD date")
    elif parsed_review_date > date.today():
        errors.append(f"{integration_id}: reviewed_at cannot be in the future")
    if not isinstance(entry.get("disable_procedure"), str) or not entry["disable_procedure"].strip():
        errors.append(f"{integration_id}: disable_procedure is required")
    return errors


def _discover_runtime_surfaces(tracked: list[Path]) -> set[str]:
    surfaces: set[str] = set()
    for path in tracked:
        rel = path.relative_to(ROOT).as_posix()
        if path.name.lower() in CONFIG_NAMES:
            surfaces.add(rel)
            continue

        if path.name == "package.json":
            try:
                package = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            deps: dict[str, object] = {}
            for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                value = package.get(key)
                if isinstance(value, dict):
                    deps.update(value)
            if any(name.lower() in SDK_DEPENDENCIES or "modelcontextprotocol" in name.lower() for name in deps):
                surfaces.add(rel)
            continue

        lower_name = path.name.lower()
        if lower_name.startswith("requirements") and lower_name.endswith((".txt", ".in")):
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for raw in lines:
                line = raw.split("#", 1)[0].strip().lower()
                package = re.split(r"[<>=!~\[; ]", line, 1)[0]
                if package in SDK_DEPENDENCIES or "modelcontextprotocol" in package:
                    surfaces.add(rel)
                    break
    return surfaces


def validate() -> list[str]:
    errors: list[str] = []
    registry = _load_registry()
    seen_ids: set[str] = set()
    seen_tools: set[str] = set()
    approved_paths: set[str] = set()

    for entry in registry["integrations"]:
        if not isinstance(entry, dict):
            errors.append("registry entries must be objects")
            continue
        errors.extend(_validate_entry(entry, seen_ids, seen_tools))
        if entry.get("status") == "approved":
            approved_paths.update(entry.get("config_paths") or [])

    tracked = _tracked_files()
    discovered = _discover_runtime_surfaces(tracked)
    unregistered = sorted(discovered.difference(approved_paths))
    for path in unregistered:
        errors.append(
            f"unregistered external tool runtime/config surface detected: {path}; "
            "review and add an approved registry entry before enablement"
        )

    missing_paths = sorted(
        path for path in approved_paths
        if not (ROOT / path).is_file()
    )
    for path in missing_paths:
        errors.append(f"approved registry config_path does not exist: {path}")

    return errors


def main() -> int:
    try:
        errors = validate()
    except (PolicyError, subprocess.CalledProcessError) as exc:
        print(f"Tool integration security gate FAILED: {exc}")
        return 1

    if errors:
        print("Tool integration security gate FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Tool integration security gate PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
