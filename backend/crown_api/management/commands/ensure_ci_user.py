"""
Management command: ensure_ci_user

Creates or updates the CrownUser row used by CI smoke testing.
Safe to run repeatedly — fully idempotent.

Reads from environment variables:
  CI_SMOKE_USERNAME   -- email of the CI user (required)
  CI_SMOKE_PASSWORD   -- plaintext password, will be hashed (required)
  CI_SMOKE_SCHOOL_ID  -- school UUID (optional)

Called automatically from startup.sh when CI_SMOKE_USERNAME is set.
"""
import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from crown_api.auth_models import CrownUser


class Command(BaseCommand):
    help = "Create or update CrownUser for CI smoke testing (reads CI_SMOKE_* env vars)"

    def handle(self, *args, **options):
        email = os.environ.get("CI_SMOKE_USERNAME", "").strip().lower()
        password = os.environ.get("CI_SMOKE_PASSWORD", "").strip()
        school_id_raw = os.environ.get("CI_SMOKE_SCHOOL_ID", "").strip()
        school_id = school_id_raw if school_id_raw else None

        if not email or not password:
            self.stdout.write(
                "ensure_ci_user: CI_SMOKE_USERNAME or CI_SMOKE_PASSWORD not set — skipping"
            )
            return

        password_hash = make_password(password)

        user, created = CrownUser.objects.update_or_create(
            email=email,
            defaults={
                "password_hash": password_hash,
                "school_id": school_id,
                "role": "director",
                "is_active": True,
            },
        )

        verb = "Created" if created else "Updated"
        self.stdout.write(
            f"ensure_ci_user: {verb} CrownUser {email} (school_id={school_id})"
        )
