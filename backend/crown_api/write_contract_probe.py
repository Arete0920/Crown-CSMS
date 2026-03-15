import json
from pathlib import Path

from django.test import Client

from crown_api.authenticated_contract_probe import create_probe_user
from crown_api.tenant_seed_adapter import (
    attach_user_to_school_if_possible,
    resolve_probe_school_context,
)
from crown_api.write_probe_adapter import (
    build_override_payload,
    build_payload_from_options_metadata,
)

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONTRACT_PATH = ROOT / "contracts" / "shell_backend_contract.json"

DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS = {"object"}


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


def get_write_probe_entries():
    contract = load_shell_backend_contract()
    entries = []

    for entry in contract.get("wizards", []):
        if not bool(entry.get("requiresWriteProof", False)):
            continue

        api_prefix = str(entry.get("apiPrefix") or "").strip()
        if not api_prefix:
            continue

        entries.append(
            {
                "moduleKey": str(entry.get("moduleKey") or "").strip(),
                "path": normalize_path(entry.get("path")),
                "apiPrefix": api_prefix,
                "writeProbeMethod": str(entry.get("writeProbeMethod") or "POST").upper(),
                "requiresAuth": bool(entry.get("requiresAuth", True)),
                "requiresSchoolHeader": bool(entry.get("requiresSchoolHeader", True)),
                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
                "probeSchoolId": str(entry.get("probeSchoolId") or "1").strip(),
                "acceptableWriteStatusCodes": list(entry.get("acceptableWriteStatusCodes") or [200, 201]),
                "expectedWriteJsonTopLevelKinds": list(
                    entry.get("expectedWriteJsonTopLevelKinds") or sorted(DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS)
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


def _request_options_metadata(client, api_prefix, extra):
    response = client.options(api_prefix, **extra)
    content_type = _get_content_type(response)
    payload = None
    errors = []

    if int(response.status_code) == 200 and "application/json" in content_type.lower():
        try:
            payload = _parse_json_response(response)
        except Exception as exc:
            errors.append(f"OPTIONS metadata JSON parse failed: {exc}")

    return {
        "statusCode": int(response.status_code),
        "contentType": content_type,
        "payload": payload,
        "errors": errors,
    }


def _validate_write_response(response, expected_json_kinds):
    status_code = int(response.status_code)
    content_type = _get_content_type(response)
    json_kind = None
    payload = None
    errors = []

    if status_code == 404:
        errors.append("write endpoint returned 404")
    if status_code >= 500:
        errors.append("write endpoint returned 5xx")
    if status_code in {301, 302, 303, 307, 308}:
        errors.append("write endpoint redirected instead of returning API response")

    if status_code in {200, 201}:
        if "application/json" not in content_type.lower():
            errors.append(f"write response was success but non-JSON content type: {content_type}")
        else:
            try:
                payload = _parse_json_response(response)
            except Exception as exc:
                errors.append(f"write success response JSON parsing failed: {exc}")
            else:
                json_kind = _get_json_kind(payload)
                if json_kind not in set(expected_json_kinds):
                    errors.append(
                        f"write response JSON kind '{json_kind}' not in expected {sorted(set(expected_json_kinds))}"
                    )

    return {
        "statusCode": status_code,
        "contentType": content_type,
        "jsonKind": json_kind,
        "payload": payload,
        "errors": errors,
    }


def execute_write_contract_entry(entry, client=None, user=None, school_context=None):
    api_prefix = str(entry.get("apiPrefix") or "").strip()
    method = str(entry.get("writeProbeMethod") or "POST").upper()
    requires_auth = bool(entry.get("requiresAuth", True))
    requires_school_header = bool(entry.get("requiresSchoolHeader", True))
    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
    probe_school_id = str(entry.get("probeSchoolId") or "1").strip()
    acceptable_write_status_codes = set(entry.get("acceptableWriteStatusCodes") or [200, 201])
    expected_json_kinds = set(entry.get("expectedWriteJsonTopLevelKinds") or ["object"])

    probe_client = client or Client(HTTP_HOST="127.0.0.1")
    probe_user = user or create_probe_user()
    effective_school_context = school_context or resolve_probe_school_context(default_school_id=probe_school_id)
    effective_school_id = str(effective_school_context.get("schoolId") or probe_school_id)
    attached_fields = attach_user_to_school_if_possible(probe_user, effective_school_context)

    if requires_auth:
        probe_client.force_login(probe_user)

    extra = {
        "HTTP_ACCEPT": "application/json",
    }

    if requires_school_header:
        extra[to_wsgi_header_name(school_header_name)] = effective_school_id

    options_result = _request_options_metadata(probe_client, api_prefix, extra)

    override_payload = build_override_payload(
        entry.get("moduleKey"),
        school_context=effective_school_context,
        user=probe_user,
    )

    payload_source = "override" if override_payload is not None else "options"
    missing_required_fields = []
    payload = override_payload

    if payload is None:
        options_payload_result = build_payload_from_options_metadata(
            entry.get("moduleKey"),
            options_result.get("payload") or {},
            school_context=effective_school_context,
            user=probe_user,
        )
        payload = options_payload_result["payload"]
        missing_required_fields = options_payload_result["missingRequiredFields"]

    errors = []
    errors.extend(options_result["errors"])

    if effective_school_context.get("seedMode") == "fallback":
        errors.append(
            f"school context fell back to default value ({effective_school_context.get('reason') or 'no reason'})"
        )

    if missing_required_fields:
        errors.append(f"missing required write fields from options metadata: {missing_required_fields}")

    if not isinstance(payload, dict):
        errors.append("write payload could not be built")
    elif payload_source != "override" and len(payload) == 0:
        errors.append("write payload could not be built")

    if errors:
        return {
            "moduleKey": entry.get("moduleKey"),
            "path": entry.get("path"),
            "apiPrefix": api_prefix,
            "writeProbeMethod": method,
            "payloadSource": payload_source,
            "payloadKeys": sorted(list(payload.keys())) if isinstance(payload, dict) else [],
            "requestedProbeSchoolId": probe_school_id,
            "effectiveProbeSchoolId": effective_school_id,
            "schoolSeedMode": effective_school_context.get("seedMode"),
            "schoolModelLabel": effective_school_context.get("schoolModelLabel"),
            "userAttachedFields": attached_fields,
            "optionsStatusCode": options_result["statusCode"],
            "optionsContentType": options_result["contentType"],
            "writeStatusCode": None,
            "writeContentType": "",
            "writeJsonKind": None,
            "writeResponsePayload": None,
            "errors": errors,
        }

    response = probe_client.generic(
        method,
        api_prefix,
        data=json.dumps(payload),
        content_type="application/json",
        **extra,
    )

    validation = _validate_write_response(response, expected_json_kinds)
    status_code = validation["statusCode"]

    if status_code not in acceptable_write_status_codes:
        validation["errors"].append(
            f"write status {status_code} not in acceptable set {sorted(acceptable_write_status_codes)}"
        )

    return {
        "moduleKey": entry.get("moduleKey"),
        "path": entry.get("path"),
        "apiPrefix": api_prefix,
        "writeProbeMethod": method,
        "payloadSource": payload_source,
        "payloadKeys": sorted(list(payload.keys())),
        "requestedProbeSchoolId": probe_school_id,
        "effectiveProbeSchoolId": effective_school_id,
        "schoolSeedMode": effective_school_context.get("seedMode"),
        "schoolModelLabel": effective_school_context.get("schoolModelLabel"),
        "userAttachedFields": attached_fields,
        "optionsStatusCode": options_result["statusCode"],
        "optionsContentType": options_result["contentType"],
        "writeStatusCode": validation["statusCode"],
        "writeContentType": validation["contentType"],
        "writeJsonKind": validation["jsonKind"],
        "writeResponsePayload": validation["payload"],
        "errors": validation["errors"],
    }


def probe_write_contract(client=None):
    findings = []
    base_client = client or Client(HTTP_HOST="127.0.0.1")
    school_context = resolve_probe_school_context()
    probe_user = create_probe_user()
    attach_user_to_school_if_possible(probe_user, school_context)

    for entry in get_write_probe_entries():
        findings.append(
            execute_write_contract_entry(
                entry,
                client=base_client,
                user=probe_user,
                school_context=school_context,
            )
        )

    return findings


def get_write_contract_failures(client=None):
    return [finding for finding in probe_write_contract(client) if finding["errors"]]


def get_write_contract_summary(client=None):
    findings = probe_write_contract(client)
    failures = [finding for finding in findings if finding["errors"]]

    status_counts = {}
    payload_source_counts = {}

    for finding in findings:
        code = finding["writeStatusCode"]
        source = finding["payloadSource"]

        status_counts[str(code)] = status_counts.get(str(code), 0) + 1
        payload_source_counts[str(source)] = payload_source_counts.get(str(source), 0) + 1

    return {
        "probedEntryCount": len(findings),
        "failureCount": len(failures),
        "statusCounts": status_counts,
        "payloadSourceCounts": payload_source_counts,
    }
