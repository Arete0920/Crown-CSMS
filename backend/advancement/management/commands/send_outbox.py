"""
Management command: send_outbox

Dequeues pending EmailOutbox rows and delivers them via Django's email backend.

Usage::

    python manage.py send_outbox
    python manage.py send_outbox --limit 50
    python manage.py send_outbox --dry-run

This command is safe to run concurrently: each row is selected with
select_for_update(skip_locked=True) so two workers never deliver the same email.
Schedule with a cron job or systemd timer (e.g., every 60 seconds).
"""
from __future__ import annotations

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deliver pending EmailOutbox rows via Django's email backend."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of emails to process in one run (default: 100).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List pending emails without sending them.",
        )

    def handle(self, *args, **options) -> None:
        from advancement.models_stage3_3 import EmailOutbox
        from advancement.emailer import send_outbox_email
        from django.db import transaction

        limit: int = options["limit"]
        dry_run: bool = options["dry_run"]

        pending = EmailOutbox.objects.filter(status="pending").order_by("created_at")[:limit]

        if not pending:
            self.stdout.write("No pending emails in outbox.")
            return

        sent = 0
        failed = 0

        for row in pending:
            if dry_run:
                self.stdout.write(f"[DRY-RUN] Would send: id={row.id} to={row.to_email} kind={row.kind}")
                continue

            # Acquire row-level lock (skip if another worker holds it)
            with transaction.atomic():
                try:
                    locked_row = EmailOutbox.objects.select_for_update(skip_locked=True).get(
                        id=row.id, status="pending"
                    )
                except EmailOutbox.DoesNotExist:
                    continue  # already picked up by another worker

                ok = send_outbox_email(locked_row)

            if ok:
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"  Sent id={row.id} → {row.to_email}"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  Failed id={row.id} → {row.to_email}"))

        if not dry_run:
            self.stdout.write(f"Outbox run complete: sent={sent} failed={failed}")
