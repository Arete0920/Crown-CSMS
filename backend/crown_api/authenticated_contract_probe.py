import json
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import models
from django.test import Client
from django.utils import timezone

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONTRACT_PATH = ROOT / "contracts" / "shell_backend_contract.json"

DEFAULT_PROBE_METHOD = "GET"
DEFAULT_ACCEPTABLE_MISSING_SCHOOL_HEADER_STATUS_CODES = {400, 403}
DEFAULT_ACCEPTABLE_AUTHENTICATED_STATUS_CODES = {200, 403, 405}
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


def get_authenticated_probe_entries():
    contract = load_shell_backend_contract()
    entries = []

    for entry in contract.get("wizards", []):
        api_prefix = str(entry.get("apiPrefix") or "").strip()
        if not api_prefix:
            continue

        entries.append(
            {
                "moduleKey": str(entry.get("moduleKey") or "").strip(),
                "path": normalize_path(entry.get("path")),
                "apiPrefix": api_prefix,
                "probeMethod": str(entry.get("probeMethod") or DEFAULT_PROBE_METHOD).upper(),
                "requiresAuth": bool(entry.get("requiresAuth", True)),
                "requiresSchoolHeader": bool(entry.get("requiresSchoolHeader", True)),
                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
                "probeSchoolId": str(entry.get("probeSchoolId") or "1").strip(),
                "acceptableMissingSchoolHeaderStatusCodes": list(
                    entry.get("acceptableMissingSchoolHeaderStatusCodes")
                    or sorted(DEFAULT_ACCEPTABLE_MISSING_SCHOOL_HEADER_STATUS_CODES)
                ),
                "acceptableAuthenticatedStatusCodes": list(
                    entry.get("acceptableAuthenticatedStatusCodes")
                    or sorted(DEFAULT_ACCEPTABLE_AUTHENTICATED_STATUS_CODES)
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


def _default_value_for_field(field, unique):
    if isinstance(field, (models.CharField, models.TextField, models.SlugField)):
        max_length = getattr(field, "max_length", 64) or 64
        base = f"probe_{unique}"
        return base[:max_length]

    if isinstance(field, models.EmailField):
        return f"probe_{unique}@example.com"

    if isinstance(field, models.BooleanField):
        return True

    if isinstance(field, (models.IntegerField, models.BigIntegerField, models.PositiveIntegerField)):
        return 1

    if isinstance(field, models.DateTimeField):
        return timezone.now()

    if isinstance(field, models.DateField):
        return timezone.now().date()

    if isinstance(field, models.TimeField):
        return timezone.now().time()

    return None


def create_probe_user():
    User = get_user_model()
    unique = uuid.uuid4().hex[:12]
    username_field = getattr(User, "USERNAME_FIELD", "username")

    concrete_fields = {
        field.name: field
        for field in User._meta.get_fields()
        if getattr(field, "concrete", False) and not getattr(field, "many_to_many", False)
    }

    kwargs = {}

    if username_field == "email":
        kwargs["email"] = f"probe_{unique}@example.com"
        if "username" in concrete_fields:
            kwargs["username"] = f"probe_{unique}"
    else:
        kwargs[username_field] = f"probe_{unique}"
        if "email" in concrete_fields:
            kwargs["email"] = f"probe_{unique}@example.com"

    for field_name in getattr(User, "REQUIRED_FIELDS", []):
        if field_name in kwargs:
            continue
        field = concrete_fields.get(field_name)
        if field is None:
            continue
        kwargs[field_name] = _default_value_for_field(field, unique)

    manager = User.objects
    password = f"Probe-{unique}-Pass123!"

    if hasattr(manager, "create_user"):
        try:
            user = manager.create_user(password=password, **kwargs)
        except TypeError:
            user = manager.create_user(**kwargs)
            if hasattr(user, "set_password"):
                user.set_password(password)
    else:
        user = manager.create(**kwargs)
        if hasattr(user, "set_password"):
            user.set_password(password)

    if hasattr(user, "is_active"):
        user.is_active = True
    if hasattr(user, "is_staff"):
        user.is_staff = True
    if hasattr(user, "is_superuser"):
        user.is_superuser = True

    user.save()
    return user


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

    if isinstance(payload, dict) and len(payload) == 0:
        errors.append("status 200 but JSON object is empty")

    return content_type, json_kind, errors


def probe_authenticated_contract_entry(entry, client=None, user=None):
    api_prefix = str(entry.get("apiPrefix") or "").strip()
    method = str(entry.get("probeMethod") or DEFAULT_PROBE_METHOD).upper()
    requires_auth = bool(entry.get("requiresAuth", True))
    requires_school_header = bool(entry.get("requiresSchoolHeader", True))
    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
    probe_school_id = str(entry.get("probeSchoolId") or "1").strip()
    acceptable_missing_school_header_status_codes = set(
        entry.get("acceptableMissingSchoolHeaderStatusCodes")
        or DEFAULT_ACCEPTABLE_MISSING_SCHOOL_HEADER_STATUS_CODES
    )
    acceptable_authenticated_status_codes = set(
        entry.get("acceptableAuthenticatedStatusCodes")
        or DEFAULT_ACCEPTABLE_AUTHENTICATED_STATUS_CODES
    )
    expected_json_kinds = set(
        entry.get("expectedJsonTopLevelKinds") or DEFAULT_EXPECTED_JSON_TOP_LEVEL_KINDS
    )

    probe_client = client or Client(HTTP_HOST="127.0.0.1")
    probe_user = user or create_probe_user()

    if requires_auth:
        probe_client.force_login(probe_user)

    errors = []

    missing_header_status = None
    missing_header_content_type = ""
    authenticated_status = None
    authenticated_content_type = ""
    authenticated_json_kind = None

    if requires_school_header:
        missing_header_response = probe_client.generic(
            method,
            api_prefix,
            HTTP_ACCEPT="application/json",
        )
        missing_header_status = int(missing_header_response.status_code)
        missing_header_content_type = _get_content_type(missing_header_response)

        if missing_header_status not in acceptable_missing_school_header_status_codes:
            errors.append(
                f"missing-school-header status {missing_header_status}; expected one of {sorted(acceptable_missing_school_header_status_codes)}"
            )

        if missing_header_status == 200:
            errors.append("endpoint returned 200 without required school header")

        if missing_header_status == 404:
            errors.append("endpoint returned 404 without school header")
        if missing_header_status >= 500:
            errors.append("endpoint returned 5xx without school header")
        if missing_header_status in {301, 302, 303, 307, 308}:
            errors.append("endpoint redirected without school header")

    extra = {
        "HTTP_ACCEPT": "application/json",
    }

    if requires_school_header:
        extra[to_wsgi_header_name(school_header_name)] = probe_school_id

    authenticated_response = probe_client.generic(
        method,
        api_prefix,
        **extra,
    )
    authenticated_status = int(authenticated_response.status_code)
    authenticated_content_type = _get_content_type(authenticated_response)

    if authenticated_status not in acceptable_authenticated_status_codes:
        errors.append(
            f"authenticated status {authenticated_status}; expected one of {sorted(acceptable_authenticated_status_codes)}"
        )

    if authenticated_status == 404:
        errors.append("endpoint returned 404 with auth/header")
    if authenticated_status >= 500:
        errors.append("endpoint returned 5xx with auth/header")
    if authenticated_status in {301, 302, 303, 307, 308}:
        errors.append("endpoint redirected with auth/header")

    if authenticated_status == 200:
        _, authenticated_json_kind, json_errors = _validate_json_api_response(
            authenticated_response,
            expected_json_kinds,
        )
        errors.extend(json_errors)

    return {
        "moduleKey": entry.get("moduleKey"),
        "path": entry.get("path"),
        "apiPrefix": api_prefix,
        "probeMethod": method,
        "requiresAuth": requires_auth,
        "requiresSchoolHeader": requires_school_header,
        "schoolHeaderName": school_header_name,
        "probeSchoolId": probe_school_id,
        "missingSchoolHeaderStatusCode": missing_header_status,
        "missingSchoolHeaderContentType": missing_header_content_type,
        "authenticatedStatusCode": authenticated_status,
        "authenticatedContentType": authenticated_content_type,
        "authenticatedJsonKind": authenticated_json_kind,
        "errors": errors,
    }


def probe_authenticated_contract(client=None):
    findings = []
    base_client = client or Client(HTTP_HOST="127.0.0.1")
    probe_user = create_probe_user()

    for entry in get_authenticated_probe_entries():
        findings.append(
            probe_authenticated_contract_entry(
                entry,
                client=base_client,
                user=probe_user,
            )
        )

    return findings


def get_authenticated_contract_failures(client=None):
    return [finding for finding in probe_authenticated_contract(client) if finding["errors"]]


def get_authenticated_contract_summary(client=None):
    findings = probe_authenticated_contract(client)
    failures = [finding for finding in findings if finding["errors"]]

    authenticated_status_counts = {}
    missing_header_status_counts = {}

    for finding in findings:
        a_code = finding["authenticatedStatusCode"]
        m_code = finding["missingSchoolHeaderStatusCode"]

        authenticated_status_counts[str(a_code)] = authenticated_status_counts.get(str(a_code), 0) + 1
        missing_header_status_counts[str(m_code)] = missing_header_status_counts.get(str(m_code), 0) + 1

    return {
        "probedEntryCount": len(findings),
        "failureCount": len(failures),
        "authenticatedStatusCounts": authenticated_status_counts,
        "missingHeaderStatusCounts": missing_header_status_counts,
    }
