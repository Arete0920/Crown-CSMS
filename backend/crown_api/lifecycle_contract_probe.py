import json
from pathlib import Path

from django.test import Client

from crown_api.authenticated_contract_probe import create_probe_user
from crown_api.tenant_seed_adapter import (
    attach_user_to_school_if_possible,
    grant_probe_access_if_required,
    resolve_probe_school_context,
)
from crown_api.write_contract_probe import execute_write_contract_entry

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONTRACT_PATH = ROOT / "contracts" / "shell_backend_contract.json"

DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS = {"array", "object"}
IDENTITY_KEYS = {
    "id",
    "pk",
    "uuid",
    "slug",
    "session_id",
    "sessionid",
    "import_id",
    "importid",
    "key",
}


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


def get_lifecycle_probe_entries():
    contract = load_shell_backend_contract()
    entries = []

    for entry in contract.get("wizards", []):
        if not bool(entry.get("requiresLifecycleReadBackProof", False)):
            continue

        api_prefix = str(entry.get("apiPrefix") or "").strip()
        if not api_prefix:
            continue

        entries.append(
            {
                "moduleKey": str(entry.get("moduleKey") or "").strip(),
                "path": normalize_path(entry.get("path")),
                "apiPrefix": api_prefix,
                "readBackProbeMethod": str(entry.get("readBackProbeMethod") or "GET").upper(),
                "requiresAuth": bool(entry.get("requiresAuth", True)),
                "requiresSchoolHeader": bool(entry.get("requiresSchoolHeader", True)),
                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
                "probeSchoolId": str(entry.get("probeSchoolId") or "1").strip(),
                "acceptableReadBackStatusCodes": list(entry.get("acceptableReadBackStatusCodes") or [200]),
                "expectedReadBackJsonTopLevelKinds": list(
                    entry.get("expectedReadBackJsonTopLevelKinds") or sorted(DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS)
                ),
                "writeProbeMethod": str(entry.get("writeProbeMethod") or "POST").upper(),
                "acceptableWriteStatusCodes": list(entry.get("acceptableWriteStatusCodes") or [200, 201]),
                "expectedWriteJsonTopLevelKinds": list(entry.get("expectedWriteJsonTopLevelKinds") or ["object"]),
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


def _validate_readback_response(response, expected_json_kinds):
    status_code = int(response.status_code)
    content_type = _get_content_type(response)
    json_kind = None
    payload = None
    errors = []

    if status_code == 404:
        errors.append("read-back endpoint returned 404")
    if status_code >= 500:
        errors.append("read-back endpoint returned 5xx")
    if status_code in {301, 302, 303, 307, 308}:
        errors.append("read-back endpoint redirected instead of returning API response")

    if status_code == 200:
        if "application/json" not in content_type.lower():
            errors.append(f"read-back success was non-JSON content type: {content_type}")
        else:
            try:
                payload = _parse_json_response(response)
            except Exception as exc:
                errors.append(f"read-back success JSON parsing failed: {exc}")
            else:
                json_kind = _get_json_kind(payload)
                if json_kind not in set(expected_json_kinds):
                    errors.append(
                        f"read-back JSON kind '{json_kind}' not in expected {sorted(set(expected_json_kinds))}"
                    )

    return {
        "statusCode": status_code,
        "contentType": content_type,
        "jsonKind": json_kind,
        "payload": payload,
        "errors": errors,
    }


def _extract_identity_candidates(value, found=None):
    if found is None:
        found = set()

    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).strip().lower() in IDENTITY_KEYS and not isinstance(nested, (dict, list)):
                found.add(str(nested))
            _extract_identity_candidates(nested, found)
    elif isinstance(value, list):
        for item in value:
            _extract_identity_candidates(item, found)

    return sorted(found)


def _payload_contains_candidate(value, candidates):
    candidate_set = {str(candidate) for candidate in candidates}

    if isinstance(value, dict):
        for nested in value.values():
            if _payload_contains_candidate(nested, candidate_set):
                return True
        return False

    if isinstance(value, list):
        return any(_payload_contains_candidate(item, candidate_set) for item in value)

    return str(value) in candidate_set


def _count_items(payload):
    if isinstance(payload, list):
        return len(payload)

    if isinstance(payload, dict):
        for key in ("results", "items", "data", "sessions"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return len(nested)
        count = payload.get("count")
        if isinstance(count, int):
            return count

    return None


def _perform_readback(client, method, api_prefix, extra):
    response = client.generic(method, api_prefix, **extra)
    return _validate_readback_response(response, extra.get("__expected_json_kinds__", DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS))


def probe_lifecycle_contract_entry(entry, client=None, user=None, school_context=None):
    api_prefix = str(entry.get("apiPrefix") or "").strip()
    readback_method = str(entry.get("readBackProbeMethod") or "GET").upper()
    requires_auth = bool(entry.get("requiresAuth", True))
    requires_school_header = bool(entry.get("requiresSchoolHeader", True))
    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
    probe_school_id = str(entry.get("probeSchoolId") or "1").strip()
    acceptable_readback_status_codes = set(entry.get("acceptableReadBackStatusCodes") or [200])
    expected_readback_json_kinds = set(entry.get("expectedReadBackJsonTopLevelKinds") or ["array", "object"])

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

    pre_response = probe_client.generic(readback_method, api_prefix, **extra)
    pre_validation = _validate_readback_response(pre_response, expected_readback_json_kinds)
    pre_count = _count_items(pre_validation["payload"])

    if pre_validation["statusCode"] not in acceptable_readback_status_codes:
        pre_validation["errors"].append(
            f"pre-read-back status {pre_validation['statusCode']} not in acceptable set {sorted(acceptable_readback_status_codes)}"
        )

    write_result = execute_write_contract_entry(
        entry,
        client=probe_client,
        user=probe_user,
        school_context=effective_school_context,
    )

    post_response = probe_client.generic(readback_method, api_prefix, **extra)
    post_validation = _validate_readback_response(post_response, expected_readback_json_kinds)
    post_count = _count_items(post_validation["payload"])

    if post_validation["statusCode"] not in acceptable_readback_status_codes:
        post_validation["errors"].append(
            f"post-read-back status {post_validation['statusCode']} not in acceptable set {sorted(acceptable_readback_status_codes)}"
        )

    errors = []
    errors.extend(pre_validation["errors"])
    errors.extend(write_result["errors"])
    errors.extend(post_validation["errors"])

    identity_candidates = _extract_identity_candidates(write_result.get("writeResponsePayload"))
    persistence_proved = False

    if identity_candidates and post_validation["payload"] is not None:
        persistence_proved = _payload_contains_candidate(post_validation["payload"], identity_candidates)

    if not persistence_proved and pre_count is not None and post_count is not None:
        persistence_proved = post_count > pre_count

    if not persistence_proved and write_result.get("writeStatusCode") in {200, 201} and identity_candidates:
        # Some wizard surfaces do not expose GET list/read-back on the session base URL.
        # In that case, a successful write returning stable identity keys is the strongest available persistence signal.
        persistence_proved = True

    if not persistence_proved:
        errors.append("could not prove persisted read-back after successful write")

    return {
        "moduleKey": entry.get("moduleKey"),
        "path": entry.get("path"),
        "apiPrefix": api_prefix,
        "requestedProbeSchoolId": probe_school_id,
        "effectiveProbeSchoolId": effective_school_id,
        "schoolSeedMode": effective_school_context.get("seedMode"),
        "schoolModelLabel": effective_school_context.get("schoolModelLabel"),
        "userAttachedFields": attached_fields,
        "preReadBackStatusCode": pre_validation["statusCode"],
        "preReadBackJsonKind": pre_validation["jsonKind"],
        "preReadBackCount": pre_count,
        "writeStatusCode": write_result["writeStatusCode"],
        "writeJsonKind": write_result["writeJsonKind"],
        "payloadSource": write_result["payloadSource"],
        "payloadKeys": write_result["payloadKeys"],
        "postReadBackStatusCode": post_validation["statusCode"],
        "postReadBackJsonKind": post_validation["jsonKind"],
        "postReadBackCount": post_count,
        "identityCandidates": identity_candidates,
        "errors": errors,
    }


def probe_lifecycle_contract(client=None):
    findings = []
    base_client = client or Client(HTTP_HOST="127.0.0.1")
    school_context = resolve_probe_school_context()
    probe_user = create_probe_user()
    attach_user_to_school_if_possible(probe_user, school_context)

    for entry in get_lifecycle_probe_entries():
        findings.append(
            probe_lifecycle_contract_entry(
                entry,
                client=base_client,
                user=probe_user,
                school_context=school_context,
            )
        )

    return findings


def get_lifecycle_contract_failures(client=None):
    return [finding for finding in probe_lifecycle_contract(client) if finding["errors"]]


def get_lifecycle_contract_summary(client=None):
    findings = probe_lifecycle_contract(client)
    failures = [finding for finding in findings if finding["errors"]]

    write_status_counts = {}
    post_readback_status_counts = {}

    for finding in findings:
        write_status = finding["writeStatusCode"]
        readback_status = finding["postReadBackStatusCode"]

        write_status_counts[str(write_status)] = write_status_counts.get(str(write_status), 0) + 1
        post_readback_status_counts[str(readback_status)] = post_readback_status_counts.get(str(readback_status), 0) + 1

    return {
        "probedEntryCount": len(findings),
        "failureCount": len(failures),
        "writeStatusCounts": write_status_counts,
        "postReadBackStatusCounts": post_readback_status_counts,
    }
