"""Non-shared credentials for explicitly authorized local Heritage fixtures.

Evaluator-facing sandbox sessions use a separate, passwordless mechanism.
The old CROWN_DEMO_PASSWORD is not used for these school accounts.
"""

from __future__ import annotations

import os

from django.core.management.base import CommandError


# Keys are existing local fixture usernames; values are secret-store environment
# names. Do not publish values, accept secrets as CLI arguments, or provide defaults.
DEMO_ACCOUNT_PASSWORD_VARIABLES = {
    "head@crown-demo.local": "CROWN_DEMO_HEAD_PASSWORD",
    "finance@crown-demo.local": "CROWN_DEMO_FINANCE_PASSWORD",
    "aid@crown-demo.local": "CROWN_DEMO_AID_PASSWORD",
    "registrar@crown-demo.local": "CROWN_DEMO_REGISTRAR_PASSWORD",
    "teacher": "CROWN_DEMO_TEACHER_PASSWORD",
    "parent": "CROWN_DEMO_PARENT_PASSWORD",
}


def configured_demo_passwords(*, require_complete: bool = False) -> dict[str, str]:
    """Return distinct, validated per-account secrets supplied by the operator.

    No password variables means account seeding disables password login.
    A reset requires the complete set; an invalid or duplicate secret fails
    closed before any user record is modified. Error text never prints secrets.
    """
    found: dict[str, str] = {}
    used: set[str] = set()
    old_shared_password = os.getenv("CROWN_DEMO_PASSWORD")

    for username, setting in DEMO_ACCOUNT_PASSWORD_VARIABLES.items():
        password = os.getenv(setting)
        if password is None:
            continue
        if (
            not 16 <= len(password) <= 256
            or password != password.strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in password)
            or password.casefold() in {"demo1234", "password", "changeme", "admin1234"}
        ):
            raise CommandError(
                f"{setting} must be a 16-256 character secret without "
                "surrounding whitespace or control characters."
            )
        if password in used or (
            old_shared_password is not None and password == old_shared_password
        ):
            raise CommandError(
                "Local Heritage account passwords must be distinct from one "
                "another and from the retired shared demo password."
            )
        used.add(password)
        found[username] = password

    if require_complete and len(found) != len(DEMO_ACCOUNT_PASSWORD_VARIABLES):
        raise CommandError(
            "Explicit reset requires all six distinct CROWN_DEMO_*_PASSWORD "
            "account secrets; CROWN_DEMO_PASSWORD is not supported."
        )
    return found
