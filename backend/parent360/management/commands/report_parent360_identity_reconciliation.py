from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from parent360.reconciliation import build_identity_reconciliation_report


class Command(BaseCommand):
    help = (
        "Emit a read-only Parent360 Guardian/account reconciliation report. "
        "The command never creates, changes, or infers authorization links."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            dest="school_id",
            help="Optional school UUID used to limit the report.",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Indent JSON output for human review.",
        )
        parser.add_argument(
            "--fail-on-conflicts",
            action="store_true",
            help=(
                "Exit non-zero when cross-tenant or canonical-identity conflicts are present. "
                "The report remains read-only."
            ),
        )

    def handle(self, *args, **options):
        report = build_identity_reconciliation_report(school_id=options.get("school_id"))
        self.stdout.write(
            json.dumps(
                report,
                indent=2 if options.get("pretty") else None,
                sort_keys=True,
            )
        )

        if options.get("fail_on_conflicts"):
            summary = report["summary"]
            conflict_total = summary.get("cross_tenant", 0) + summary.get(
                "canonical_identity_conflict", 0
            )
            if conflict_total:
                raise CommandError(
                    f"Parent360 identity reconciliation found {conflict_total} conflict record(s)."
                )
