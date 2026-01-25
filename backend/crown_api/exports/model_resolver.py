from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Type

from django.apps import apps
from django.db import models


@dataclass(frozen=True)
class ModelCandidate:
    app_label: str
    model_name: str


class ModelNotFound(RuntimeError):
    pass


def resolve_model(candidates: Sequence[ModelCandidate]) -> Type[models.Model]:
    """Resolve a Django model by trying multiple (app_label, model_name) candidates.

    This avoids brittle imports during spine evolution.
    """

    for c in candidates:
        try:
            m = apps.get_model(c.app_label, c.model_name)
        except LookupError:
            m = None
        if m is not None:
            return m
    raise ModelNotFound(
        "Could not resolve model. Tried: "
        + ", ".join([f"{c.app_label}.{c.model_name}" for c in candidates])
    )


def default_export_fields(model: Type[models.Model]) -> list[str]:
    """Export stable, non-sensitive fields.

    - Includes concrete DB fields
    - Excludes common secrets/tokens and large blobs
    """

    exclude_names = {
        "password",
        "last_login",
        "is_superuser",
        "user_permissions",
        "groups",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "private_key",
        "ssn",
        "social_security_number",
        "medical",
        "notes_private",
        "blob",
        "photo",
        "image",
        "document",
        "file",
    }

    fields: list[str] = []
    for f in model._meta.get_fields():
        if not getattr(f, "concrete", False):
            continue
        name = getattr(f, "name", None)
        if not name:
            continue
        if name in exclude_names:
            continue
        fields.append(name)

    return fields
