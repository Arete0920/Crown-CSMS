"""
One-time lockdown: set unusable passwords on all sandbox demo persona accounts.

Removes any legacy shared demo password from existing UserAccount rows so the
no-login sandbox session flow (POST /api/v1/sandbox/session/) is the only entry
path for demo personas. Safe to re-run (idempotent). Supports --dry-run.

Usage:
    python manage.py sandbox_lockdown_personas --dry-run
    python manage.py sandbox_lockdown_personas
"""
from django.core.management.base import BaseCommand

from core.models import UserAccount
from sandbox_demo.catalog import SANDBOX_PERSONAS

class Command(BaseCommand):
    help = "Set unusable passwords on all sandbox demo persona accounts (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        persona_emails = sorted({p.email for p in SANDBOX_PERSONAS.values()})

        locked = 0
        already = 0
        missing = []

        for email in persona_emails:
            user = UserAccount.objects.filter(username=email).first()
            if user is None:
                missing.append(email)
                continue
            if not user.has_usable_password():
                already += 1
                self.stdout.write(f"OK   already-unusable: {email}")
                continue
            if dry_run:
                self.stdout.write(f"PLAN would-lock: {email}")
            else:
                user.set_unusable_password()
                user.save(update_fields=["password"])
                self.stdout.write(f"LOCK locked: {email}")
            locked += 1

        for email in missing:
            self.stdout.write(f"SKIP not-found: {email}")

        verb = "would lock" if dry_run else "locked"
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {verb}: {locked}, already unusable: {already}, "
                f"not found: {len(missing)}, personas checked: {len(persona_emails)}."
            )
        )
        if not dry_run and locked == 0 and already == len(persona_emails) - len(missing):
            self.stdout.write(self.style.SUCCESS("All existing persona accounts are password-locked."))
