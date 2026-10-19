"""Credential policy shared by local demonstration management commands.

Evaluator-facing Heritage sandbox sessions remain passwordless and are not
provisioned through this setting.
"""

from __future__ import annotations

import os

from django.core.management.base import CommandError


def configured_demo_password() -> str | None:
    """Return an explicitly configured long password, or disable password logins.

    Known weak or malformed configuration is an error, not a reason to fall
    back to a baked-in password. Never include the supplied secret in errors.
    """
    password = os.getenv("CROWN_DEMO_PASSWORD", "")
    if not password:
        return None
    if (
        len(password) < 16
        or len(password) > 256
        or password != password.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in password)
        or password.casefold() in {"demo1234", "password", "changeme", "admin1234"}
    ):
        raise CommandError(
            "CROWN_DEMO_PASSWORD must be a nonblank 16-256 character secret "
            "without surrounding whitespace or control characters."
        )
    return password
