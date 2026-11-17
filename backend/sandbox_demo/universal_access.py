"""Opt-in credentials for newly created fictional presenter accounts only."""
import os

from django.core.management.base import CommandError
from django.db import transaction

from .catalog import SANDBOX_PERSONAS
from .universal_identity import presenter_username


def presenter_passwords():
    """Validate all per-role operator secrets without logging any value."""
    passwords = {}
    for key in SANDBOX_PERSONAS:
        value = os.environ.get(f"CROWN_PRESENTER_{key.upper()}_PASSWORD", "")
        if (not 20 <= len(value) <= 256 or value != value.strip()
                or any(ord(char) < 33 or ord(char) == 127 for char in value)
                or len(set(value)) < 8):
            raise CommandError("Presenter login requires a distinct 20–256 character operator secret for every persona; no values were logged.")
        passwords[key] = value
    if len(set(passwords.values())) != len(passwords):
        raise CommandError("Presenter persona secrets must be distinct; no values were logged.")
    return passwords


def initialize_presenter_passwords(school, passwords):
    # Only called inside the initial seed/reset transaction. Never provides a
    # standalone password-rotation command or changes an existing principal.
    from core.models import UserAccount
    from .universal_demo import _owned_school
    from .universal_runtime import require_presenter_runtime
    require_presenter_runtime()
    if passwords != presenter_passwords():
        raise CommandError("Presenter credential initialization requires validated operator secrets.")
    with transaction.atomic():
        owned = _owned_school()
        if owned is None or owned.pk != school.pk:
            raise CommandError("Presenter credential initialization requires its owned school and validated operator secrets.")
        for key, password in passwords.items():
            account = UserAccount.objects.get(school=school, username=presenter_username(key, school.pk))
            if account.has_usable_password() or account.is_staff or account.is_superuser:
                raise CommandError("Presenter credential initialization refused an existing or privileged login.")
            account.set_password(password)
            account.save(update_fields=["password"])
