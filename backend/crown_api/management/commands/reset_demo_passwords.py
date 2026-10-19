"""Reset only the explicitly selected fictional Heritage demonstration accounts."""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.demo_credentials import configured_demo_passwords
from core.demo_seed_safety import require_local_demo_seed
from core.models import School, UserRole


DEMO_USERNAMES = (
    "head@crown-demo.local",
    "finance@crown-demo.local",
    "aid@crown-demo.local",
    "registrar@crown-demo.local",
)
EXTRA_DEMO_USERS = (
    {"username": "teacher", "email": "teacher@crown-demo.local", "role_code": "TEACHER"},
    {"username": "parent", "email": "parent@crown-demo.local", "role_code": "PARENT"},
)


class Command(BaseCommand):
    help = "Reset selected Heritage demo accounts using distinct per-account secrets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            default=None,
            help="Heritage demo school UUID; required unless CROWN_DEMO_SCHOOL_ID is set.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        require_local_demo_seed(operation="password reset")
        passwords = configured_demo_passwords(require_complete=True)

        school_id = options.get("school_id") or os.environ.get("CROWN_DEMO_SCHOOL_ID")
        if not school_id:
            raise CommandError("--school-id or CROWN_DEMO_SCHOOL_ID is required.")
        try:
            school = School.objects.get(pk=school_id)
        except (School.DoesNotExist, ValidationError, ValueError) as exc:
            raise CommandError("Specified demo school does not exist.") from exc
        if school.name != "Heritage Christian Academy":
            raise CommandError("Only the Heritage Christian Academy demo school is supported.")

        User = get_user_model()
        target_usernames = (*DEMO_USERNAMES, *(spec["username"] for spec in EXTRA_DEMO_USERS))
        existing = {user.username: user for user in User.objects.filter(username__in=target_usernames)}
        expected_emails = {
            **{username: username for username in DEMO_USERNAMES},
            **{spec["username"]: spec["email"] for spec in EXTRA_DEMO_USERS},
        }

        # Perform all cross-school and identity checks before modifying accounts.
        for username, user in existing.items():
            if user.school_id != school.pk:
                raise CommandError(
                    f"Refusing demo password reset: {username} belongs to another school."
                )
            if user.email != expected_emails[username]:
                raise CommandError(
                    f"Refusing demo password reset: identity mismatch for {username}."
                )

        changed = 0
        missing = []
        created = 0

        for username in DEMO_USERNAMES:
            user = existing.get(username)
            if user is None:
                missing.append(username)
                continue
            user.set_password(passwords[username])
            user.is_superuser = False
            user.is_staff = False
            user.save(update_fields=["password", "is_superuser", "is_staff"])
            changed += 1

        for spec in EXTRA_DEMO_USERS:
            user = existing.get(spec["username"])
            if user is None:
                user = User(
                    username=spec["username"],
                    school=school,
                    email=spec["email"],
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                created += 1

            user.set_password(passwords[spec['username']])
            user.is_superuser = False
            user.is_staff = False
            user.is_active = True
            user.save()
            UserRole.objects.get_or_create(
                school=school,
                user=user,
                role_code=spec["role_code"],
            )
            changed += 1

        self.stdout.write(self.style.SUCCESS(f"Reset passwords for {changed} Heritage demo users."))
        self.stdout.write(self.style.SUCCESS(f"Created missing teacher/parent users: {created}."))
        if missing:
            self.stdout.write(
                self.style.WARNING(f"Missing legacy demo accounts (not modified): {missing}")
            )
