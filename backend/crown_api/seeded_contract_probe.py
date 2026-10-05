import json
from pathlib import Path

from django.test import Client

from crown_api.authenticated_contract_probe import create_probe_user
from crown_api.tenant_seed_adapter import (
    attach_user_to_school_if_possible,
    grant_probe_access_if_required,
    resolve_probe_school_context,
)

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONTRACT_PATH = ROOT / "contracts" / "shell_backend_contract.json"

DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS = {"object", "array"}


def load_shell_backend_contract():
    return json.loads(CANONICAL_CONTRACT_PATH.read_text(encoding="utf-8"))


def normalize_path(value):
    path = str(value or "").strip()
    if not path:
        return ""

    if not path.startswith("/"):
        path = f"/{path}"

    while "//" in path:
        path = path.replace("//", "/")

    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    return path


def to_wsgi_header_name(header_name):
    header_name = str(header_name or "").strip()
    if not header_name:
        return ""
    return f"HTTP_{header_name.upper().replace('-', '_')}"


def get_seeded_probe_entries():
    contract = load_shell_backend_contract()
    entries = []

    for entry in contract.get("wizards", []):
        api_prefix = str(entry.get("apiPrefix") or "").strip()
        if not api_prefix:
            continue
        if not bool(entry.get("requiresSeededSuccess", False)):
            continue

        entries.append(
            {
                "moduleKey": str(entry.get("moduleKey") or "").strip(),
                "path": normalize_path(entry.get("path")),
                "apiPrefix": api_prefix,
                "probeMethod": str(entry.get("seededSuccessProbeMethod") or "GET").upper(),
                "requiresAuth": bool(entry.get("requiresAuth", True)),
                "requiresSchoolHeader": bool(entry.get("requiresSchoolHeader", True)),
                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
                "probeSchoolId": str(entry.get("probeSchoolId") or "1").strip(),
                "acceptableSeededSuccessStatusCodes": list(
                    entry.get("acceptableSeededSuccessStatusCodes") or [200]
                ),
                "expectedJsonTopLevelKinds": list(
                    entry.get("expectedJsonTopLevelKinds") or sorted(DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS)
                ),
            }
        )

    return entries


def _get_content_type(response):
    if hasattr(response, "headers"):
        return str(response.headers.get("Content-Type", "") or "")
    return str(response.get("Content-Type", "") or "")


def _parse_json_response(response):
    raw = response.content.decode(getattr(response, "charset", None) or "utf-8")
    return json.loads(raw)


def _get_json_kind(payload):
    if isinstance(payload, dict):
        return "object"
    if isinstance(payload, list):
        return "array"
    if payload is None:
        return "null"
    if isinstance(payload, bool):
        return "boolean"
    if isinstance(payload, (int, float)):
        return "number"
    if isinstance(payload, str):
        return "string"
    return type(payload).__name__


def _validate_json_api_response(response, expected_json_kinds):
    content_type = _get_content_type(response)
    json_kind = None
    errors = []

    if "application/json" not in content_type.lower():
        errors.append(f"status 200 but non-JSON content type: {content_type}")
        return content_type, json_kind, errors

    try:
        payload = _parse_json_response(response)
    except Exception as exc:
        errors.append(f"status 200 but response JSON parsing failed: {exc}")
        return content_type, json_kind, errors

    json_kind = _get_json_kind(payload)

    if json_kind not in set(expected_json_kinds):
        errors.append(
            f"unexpected JSON top-level kind '{json_kind}'; expected one of {sorted(set(expected_json_kinds))}"
        )

    return content_type, json_kind, errors


def probe_seeded_contract_entry(entry, client=None, user=None, school_context=None):
    api_prefix = str(entry.get("apiPrefix") or "").strip()
    method = str(entry.get("probeMethod") or "GET").upper()
    requires_auth = bool(entry.get("requiresAuth", True))
    requires_school_header = bool(entry.get("requiresSchoolHeader", True))
    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
    probe_school_id = str(entry.get("probeSchoolId") or "1").strip()
    acceptable_seeded_status_codes = set(entry.get("acceptableSeededSuccessStatusCodes") or [200])
    expected_json_kinds = set(entry.get("expectedJsonTopLevelKinds") or DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS)

    probe_client = client or Client(HTTP_HOST="127.0.0.1")
    probe_user = user or create_probe_user()
    effective_school_context = school_context or resolve_probe_school_context(default_school_id=probe_school_id)
    effective_school_id = str(effective_school_context.get("schoolId") or probe_school_id)
    attached_fields = attach_user_to_school_if_possible(probe_user, effective_school_context)
    grant_probe_access_if_required(entry.get("moduleKey"), probe_user, effective_school_context)

    if requires_auth:
        probe_client.force_login(probe_user)

    extra = {
        "HTTP_ACCEPT": "application/json",
    }

    if requires_school_header:
        extra[to_wsgi_header_name(school_header_name)] = effective_school_id

    response = probe_client.generic(
        method,
        api_prefix,
        **extra,
    )

    status_code = int(response.status_code)
    content_type = _get_content_type(response)
    json_kind = None
    errors = []

    if effective_school_context.get("seedMode") == "fallback":
        errors.append(
            f"could not resolve concrete school context; fallback used ({effective_school_context.get('reason') or 'no reason'})"
        )

    if status_code not in acceptable_seeded_status_codes:
        errors.append(
            f"seeded success status {status_code}; expected one of {sorted(acceptable_seeded_status_codes)}"
        )

    if status_code == 404:
        errors.append("endpoint returned 404 with seeded tenant context")
    if status_code >= 500:
        errors.append("endpoint returned 5xx with seeded tenant context")
    if status_code in {301, 302, 303, 307, 308}:
        errors.append("endpoint redirected with seeded tenant context")

    if status_code == 200:
        _, json_kind, json_errors = _validate_json_api_response(response, expected_json_kinds)
        errors.extend(json_errors)

    return {
        "moduleKey": entry.get("moduleKey"),
        "path": entry.get("path"),
        "apiPrefix": api_prefix,
        "probeMethod": method,
        "requiresAuth": requires_auth,
        "requiresSchoolHeader": requires_school_header,
        "schoolHeaderName": school_header_name,
        "requestedProbeSchoolId": probe_school_id,
        "effectiveProbeSchoolId": effective_school_id,
        "schoolSeedMode": effective_school_context.get("seedMode"),
        "schoolModelLabel": effective_school_context.get("schoolModelLabel"),
        "userAttachedFields": attached_fields,
        "statusCode": status_code,
        "contentType": content_type,
        "jsonKind": json_kind,
        "errors": errors,
    }


def probe_seeded_contract(client=None):
    findings = []
    base_client = client or Client(HTTP_HOST="127.0.0.1")
    school_context = resolve_probe_school_context()
    probe_user = create_probe_user()

    attach_user_to_school_if_possible(probe_user, school_context)

    for entry in get_seeded_probe_entries():
        findings.append(
            probe_seeded_contract_entry(
                entry,
                client=base_client,
                user=probe_user,
                school_context=school_context,
            )
        )

    return findings


def get_seeded_contract_failures(client=None):
    return [finding for finding in probe_seeded_contract(client) if finding["errors"]]


def get_seeded_contract_summary(client=None):
    findings = probe_seeded_contract(client)
    failures = [finding for finding in findings if finding["errors"]]

    status_counts = {}
    seed_mode_counts = {}

    for finding in findings:
        code = finding["statusCode"]
        mode = finding["schoolSeedMode"]

        status_counts[str(code)] = status_counts.get(str(code), 0) + 1
        seed_mode_counts[str(mode)] = seed_mode_counts.get(str(mode), 0) + 1

    return {
        "probedEntryCount": len(findings),
        "failureCount": len(failures),
        "statusCounts": status_counts,
        "seedModeCounts": seed_mode_counts,
    }
