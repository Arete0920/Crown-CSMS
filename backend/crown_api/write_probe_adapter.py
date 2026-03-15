from django.utils import timezone

COMMON_OPTIONAL_FIELDS = {
    "name",
    "title",
    "label",
    "status",
    "slug",
    "description",
    "notes",
    "wizard_slug",
    "module_key",
}

SCHOOL_FIELD_NAMES = {
    "school",
    "school_id",
    "schoolid",
    "tenant",
    "tenant_id",
    "tenantid",
    "organization",
    "organization_id",
    "organizationid",
}

USER_FIELD_NAMES = {
    "user",
    "user_id",
    "userid",
    "owner",
    "owner_id",
    "ownerid",
    "created_by",
    "created_by_id",
    "createdby",
    "createdby_id",
}

STATUS_VALUES = ("draft", "active", "open", "pending")

OVERRIDE_PAYLOAD_BUILDERS = {
    # Example:
    # "admissions-onboarding": lambda school_context, user: {"name": "Admissions Intake", "status": "draft"},
    "admissions-onboarding": lambda school_context, user: {},
    "reenrollment": lambda school_context, user: {},
    "financial-aid-setup": lambda school_context, user: {},
    "enrollment-conversion": lambda school_context, user: {},
    "enrollment-period-setup": lambda school_context, user: {},
}


def build_override_payload(module_key, school_context=None, user=None):
    builder = OVERRIDE_PAYLOAD_BUILDERS.get(str(module_key or "").strip())
    if not builder:
        return None
    return builder(school_context, user)


def _coerce_choice_value(spec):
    choices = spec.get("choices")

    if isinstance(choices, dict):
        for key in choices.keys():
            if key not in ("", None):
                return key

    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict):
                value = choice.get("value")
                if value not in ("", None):
                    return value
            elif choice not in ("", None):
                return choice

    return None


def _school_value_for_field(field_name, school_context):
    lowered = str(field_name or "").strip().lower().replace("-", "_")
    if lowered not in SCHOOL_FIELD_NAMES:
        return None

    school_id = None
    if school_context:
        school_id = school_context.get("schoolId")

    return school_id


def _user_value_for_field(field_name, user):
    lowered = str(field_name or "").strip().lower().replace("-", "_")
    if lowered not in USER_FIELD_NAMES:
        return None
    return getattr(user, "pk", None)


def _string_value_for_field(field_name):
    lowered = str(field_name or "").strip().lower()

    if "email" in lowered:
        return "probe@example.com"

    if "slug" in lowered:
        return "probe-slug"

    if lowered in {"status", "state"}:
        return STATUS_VALUES[0]

    if lowered in {"name", "title", "label"}:
        return "Probe Session"

    if lowered in {"description", "notes"}:
        return "Probe-generated payload"

    if lowered in {"wizard_slug", "wizard"}:
        return "probe-wizard"

    if lowered in {"module_key", "module"}:
        return "probe-module"

    return "probe-value"


def build_value_for_options_field(field_name, spec, school_context=None, user=None):
    school_value = _school_value_for_field(field_name, school_context)
    if school_value is not None:
        return school_value

    user_value = _user_value_for_field(field_name, user)
    if user_value is not None:
        return user_value

    choice_value = _coerce_choice_value(spec)
    if choice_value is not None:
        return choice_value

    field_type = str(spec.get("type") or "").strip().lower()
    lowered = str(field_name or "").strip().lower()

    if field_type in {"string", "text", "field", "choice"}:
        return _string_value_for_field(lowered)

    if field_type in {"integer", "number"}:
        return 1

    if field_type == "boolean":
        return True

    if field_type == "datetime":
        return timezone.now().isoformat()

    if field_type == "date":
        return timezone.now().date().isoformat()

    if field_type == "time":
        return timezone.now().time().isoformat()

    if field_type == "list":
        return []

    if field_type == "nested object":
        return {}

    return None


def build_payload_from_options_metadata(module_key, options_payload, school_context=None, user=None):
    actions = options_payload.get("actions") if isinstance(options_payload, dict) else {}
    post_schema = actions.get("POST") if isinstance(actions, dict) else None

    if not isinstance(post_schema, dict):
        return {
            "payload": {},
            "missingRequiredFields": ["__missing_post_options_schema__"],
        }

    payload = {}
    missing_required_fields = []

    for field_name, spec in post_schema.items():
        spec = spec if isinstance(spec, dict) else {}
        read_only = bool(spec.get("read_only", False))
        required = bool(spec.get("required", False))
        lowered = str(field_name or "").strip().lower()

        if read_only:
            continue

        include_field = required or lowered in COMMON_OPTIONAL_FIELDS or lowered in SCHOOL_FIELD_NAMES or lowered in USER_FIELD_NAMES
        if not include_field:
            continue

        value = build_value_for_options_field(
            field_name,
            spec,
            school_context=school_context,
            user=user,
        )

        if value is None:
            if required:
                missing_required_fields.append(field_name)
            continue

        payload[field_name] = value

    return {
        "payload": payload,
        "missingRequiredFields": sorted(set(missing_required_fields)),
    }
