"""Management command for controlled retention preview and execution."""

from django.core.management.base import BaseCommand, CommandError

from core.services.retention_service import (
    EXECUTION_CONFIRMATION,
    GLOBAL_MODEL_ALLOWLIST_SETTING,
    RetentionAuthorizationError,
    purge_expired_records,
)


class Command(BaseCommand):
    help = "Preview retention candidates or execute an explicitly authorized purge."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Perform deletion. Omit for the default non-destructive preview.",
        )
        parser.add_argument(
            "--confirm",
            dest="confirmation",
            help=f"Required with --execute; must equal {EXECUTION_CONFIRMATION!r}.",
        )
        parser.add_argument(
            "--approved-by",
            help="Required with --execute; recorded in the purge audit snapshot.",
        )
        parser.add_argument(
            "--tenant-id",
            help="Limit evaluation and deletion to one tenant or school identifier.",
        )
        parser.add_argument(
            "--allow-global",
            action="store_true",
            help=(
                "Allow only non-tenant models explicitly listed in "
                f"{GLOBAL_MODEL_ALLOWLIST_SETTING}. This cannot bypass tenant scope."
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Maximum primary records selected per deletion query (1-1000).",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        if execute and not options.get("tenant_id") and not options.get("allow_global"):
            raise CommandError(
                "--execute requires --tenant-id or the explicit --allow-global override"
            )

        mode = "EXECUTE" if execute else "DRY RUN"
        self.stdout.write(f"Starting retention {mode.lower()}...")
        try:
            results = purge_expired_records(
                execute=execute,
                confirmation=options.get("confirmation"),
                approved_by=options.get("approved_by"),
                tenant_id=options.get("tenant_id"),
                batch_size=options["batch_size"],
                allow_global=options["allow_global"],
            )
        except (RetentionAuthorizationError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        total_matched = 0
        total_deleted = 0
        for result in results:
            total_matched += result["matched"]
            total_deleted += result["deleted"]
            if result["skipped_reason"] and result["skipped_reason"] != "dry run":
                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIP    {result['model']}: {result['skipped_reason']}"
                    )
                )
            elif result["mode"] == "dry_run":
                self.stdout.write(
                    f"  PREVIEW {result['model']}: {result['matched']} records matched"
                )
            else:
                self.stdout.write(
                    f"  PURGE   {result['model']}: {result['deleted']} primary records "
                    f"deleted in {result['batches']} batches"
                )

        summary = (
            f"Retention {mode.lower()} complete. Matched: {total_matched}; "
            f"deleted: {total_deleted}."
        )
        self.stdout.write(self.style.SUCCESS(summary))
