from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

from django.http import HttpRequest


def parse_json_object(request: HttpRequest) -> dict[str, Any] | None:
    if not request.body:
        return {}

    try:
        raw_body = request.body.decode("utf-8")
    except UnicodeDecodeError:
        return None

    try:
        payload = json.loads(raw_body)
    except JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def parse_bounded_int(
    raw_value: Any,
    *,
    default: int,
    min_value: int,
    max_value: int,
) -> int:
    try:
        value = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return default

    return max(min_value, min(value, max_value))
