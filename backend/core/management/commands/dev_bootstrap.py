from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import School


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Crown2026!"
PRIMARY_SCHOOL_NAME = "Crown Demo Christian Academy"
SECONDARY_SCHOOL_NAME = "Smoke Secondary School"


class Command(BaseCommand):
    help = (
        "Local dev bootstrap: ensure schools + admin are present and linked. "
        "Safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default=DEFAULT_ADMIN_USERNAME)
        parser.add_argument("--admin-password", default=DEFAULT_ADMIN_PASSWORD)
        parser.add_argument("--primary-school", default=PRIMARY_SCHOOL_NAME)
        parser.add_argument("--secondary-school", default=SECONDARY_SCHOOL_NAME)
        parser.add_argument(
            "--no-secondary",
            action="store_true",
            help="Do not create/ensure a secondary school.",
        )

    def handle(self, *args, **options):
        admin_username = str(options["admin_username"]).strip() or DEFAULT_ADMIN_USERNAME
        admin_password = str(options["admin_password"]) or DEFAULT_ADMIN_PASSWORD
        primary_school_name = str(options["primary_school"]).strip() or PRIMARY_SCHOOL_NAME
        secondary_school_name = str(options["secondary_school"]).strip() or SECONDARY_SCHOOL_NAME
        ensure_secondary = not bool(options["no_secondary"])

        created_or_updated: list[str] = []

        # --- 1) Ensure a primary school exists (prefer the canonical name) ---
        primary_school = School.objects.filter(name=primary_school_name).first()
        if not primary_school:
            primary_school = School.objects.order_by("created_at", "id").first()

        if not primary_school:
            primary_school = School.objects.create(
                id=uuid.uuid4(),
                name=primary_school_name,
                timezone="America/New_York",
                is_active=True,
            )
            created_or_updated.append(f"school:{primary_school.name}")

        # --- 2) Ensure an optional secondary school exists ---
        secondary_school = None
        if ensure_secondary:
            secondary_school = School.objects.filter(name=secondary_school_name).first()
            if not secondary_school:
                secondary_school = School.objects.create(
                    id=uuid.uuid4(),
                    name=secondary_school_name,
                    timezone=primary_school.timezone,
                    is_active=True,
                )
                created_or_updated.append(f"school:{secondary_school.name}")

        # --- 3) Ensure admin user exists and is linked to the primary school ---
        User = get_user_model()
        admin_user, was_created = User.objects.get_or_create(username=admin_username)
        if was_created:
            created_or_updated.append("admin_user")

        admin_user.set_password(admin_password)
        admin_user.is_active = True
        admin_user.is_staff = True
        admin_user.is_superuser = True

        # UserAccount has a nullable FK `school`; keep this safe if the model changes.
        if hasattr(admin_user, "school_id") and admin_user.school_id != primary_school.id:
            admin_user.school = primary_school
            created_or_updated.append("admin_school_link")

        admin_user.save()

        # --- Output ---
        self.stdout.write(self.style.SUCCESS("dev_bootstrap complete"))
        self.stdout.write(f"Primary school: {primary_school.id} ({primary_school.name})")
        if secondary_school is not None:
            self.stdout.write(f"Secondary school: {secondary_school.id} ({secondary_school.name})")
        self.stdout.write(
            f"Admin: {admin_user.username} school_id={getattr(admin_user, 'school_id', None)}"
        )
        if created_or_updated:
            self.stdout.write("Created/updated: " + ", ".join(created_or_updated))
        else:
            self.stdout.write("No changes needed.")
