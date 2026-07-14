from __future__ import annotations

from copy import deepcopy
from inspect import signature

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from crown_api.dashboards.batch5_extra_payloads import BATCH5_EXTRA_PAYLOAD_BUILDERS
from crown_api.dashboards.models import DashboardSnapshot
from crown_api.dashboards.payload_contract import validate_dashboard_payload
from crown_api.dashboards.sample_payloads import SAMPLE_PAYLOAD_BUILDERS

ACTIVE_DASHBOARD_PAYLOAD_BUILDERS = {
    **SAMPLE_PAYLOAD_BUILDERS,
    **BATCH5_EXTRA_PAYLOAD_BUILDERS,
}

EXPECTED_ACTIVE_BUILDER_COUNT = 40

DEFAULT_SOURCE = "sample-derived-snapshot"
DEFAULT_NOTES = (
    "Seeded no-pretend dashboard snapshot. Snapshot is not live data; "
    "payload was generated from registered dashboard payload builders."
)


def builder_accepts_school_id(builder) -> bool:
    try:
        parameters = list(signature(builder).parameters.values())
    except (TypeError, ValueError):
        return True

    for parameter in parameters:
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            return True
        if parameter.name == "school_id":
            return True

    return any(
        parameter.kind in (
            parameter.POSITIONAL_ONLY,
            parameter.POSITIONAL_OR_KEYWORD,
        )
        for parameter in parameters
    )


def build_snapshot_payload(dashboard_key: str, builder, school_id: str) -> dict:
    payload = builder(school_id) if builder_accepts_school_id(builder) else builder()
    if not isinstance(payload, dict):
        raise ValueError(
            f"{dashboard_key} builder returned {type(payload).__name__}, expected dict."
        )
    payload = deepcopy(payload)
    validate_dashboard_payload(payload)
    meta = payload.setdefault("meta", {})
    original_served_from = str(meta.get("served_from") or "unknown")
    meta["served_from"] = "snapshot"
    meta["snapshot_derived_from"] = original_served_from
    meta["seeded_by"] = "seed_all_dashboard_snapshots"
    meta["seeded_at"] = timezone.now().isoformat()
    meta["seed_source"] = DEFAULT_SOURCE
    meta["no_pretend_classification"] = "snapshot"
    meta["live_certified"] = False
    meta["school_id"] = str(school_id)
    validate_dashboard_payload(payload)
    return payload


class Command(BaseCommand):
    help = (
        "Seed DashboardSnapshot rows for every active registered dashboard builder "
        "for one school."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            dest="school_id",
            required=True,
            help="School UUID or school key for school-scoped dashboard snapshots.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be written without writing rows.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Update existing snapshot rows. Default behavior skips existing rows.",
        )
        parser.add_argument(
            "--allow-count-mismatch",
            action="store_true",
            help=(
                "Do not fail if active builder count differs from the expected "
                "no-pretend baseline."
            ),
        )
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help="Row-level DashboardSnapshot.source value.",
        )
        parser.add_argument(
            "--notes",
            default=DEFAULT_NOTES,
            help="Row-level DashboardSnapshot.notes value.",
        )

    def handle(self, *args, **options):
        school_id = str(options["school_id"]).strip()
        if not school_id:
            raise CommandError("--school-id is required and cannot be blank.")

        dry_run = bool(options["dry_run"])
        overwrite = bool(options["overwrite"])
        allow_count_mismatch = bool(options["allow_count_mismatch"])
        row_source = str(options["source"]).strip() or DEFAULT_SOURCE
        row_notes = str(options["notes"]).strip() or DEFAULT_NOTES

        source_max_length = DashboardSnapshot._meta.get_field("source").max_length
        if source_max_length is not None and len(row_source) > source_max_length:
            raise CommandError(
                f"--source exceeds DashboardSnapshot.source max_length={source_max_length}."
            )

        notes_max_length = DashboardSnapshot._meta.get_field("notes").max_length
        if notes_max_length is not None and len(row_notes) > notes_max_length:
            raise CommandError(
                f"--notes exceeds DashboardSnapshot.notes max_length={notes_max_length}."
            )

        builder_count = len(ACTIVE_DASHBOARD_PAYLOAD_BUILDERS)
        if builder_count != EXPECTED_ACTIVE_BUILDER_COUNT and not allow_count_mismatch:
            raise CommandError(
                f"Active dashboard builder count is {builder_count}; "
                f"expected {EXPECTED_ACTIVE_BUILDER_COUNT}. "
                "Review builder alignment before seeding snapshots."
            )

        payloads = {}
        failed = []
        for dashboard_key in sorted(ACTIVE_DASHBOARD_PAYLOAD_BUILDERS):
            builder = ACTIVE_DASHBOARD_PAYLOAD_BUILDERS[dashboard_key]
            try:
                payloads[dashboard_key] = build_snapshot_payload(
                    dashboard_key,
                    builder,
                    school_id,
                )
            except Exception as exc:
                failed.append((dashboard_key, str(exc)))

        prefix = "[DRY-RUN] " if dry_run else ""
        if failed:
            self.stdout.write(f"{prefix}school={school_id}")
            self.stdout.write(f"{prefix}active-builders={builder_count}")
            self.stdout.write(
                f"{prefix}created=0 updated=0 skipped-existing=0 failed={len(failed)}"
            )
            for dashboard_key, error in failed:
                self.stdout.write(self.style.ERROR(f"FAILED {dashboard_key}: {error}"))
            raise CommandError(
                f"{len(failed)} dashboard payload builder(s) failed; no rows were written."
            )

        created = []
        updated = []
        skipped = []

        if dry_run:
            for dashboard_key in sorted(payloads):
                exists = DashboardSnapshot.objects.filter(
                    school_id=school_id,
                    dashboard_key=dashboard_key,
                ).exists()
                if exists and not overwrite:
                    skipped.append(dashboard_key)
                elif exists:
                    updated.append(dashboard_key)
                else:
                    created.append(dashboard_key)
        else:
            with transaction.atomic():
                for dashboard_key in sorted(payloads):
                    lookup = {
                        "school_id": school_id,
                        "dashboard_key": dashboard_key,
                    }
                    defaults = {
                        "payload": payloads[dashboard_key],
                        "source": row_source,
                        "notes": row_notes,
                    }
                    if overwrite:
                        _, was_created = DashboardSnapshot.objects.update_or_create(
                            **lookup,
                            defaults=defaults,
                        )
                        if was_created:
                            created.append(dashboard_key)
                        else:
                            updated.append(dashboard_key)
                    else:
                        _, was_created = DashboardSnapshot.objects.get_or_create(
                            **lookup,
                            defaults=defaults,
                        )
                        if was_created:
                            created.append(dashboard_key)
                        else:
                            skipped.append(dashboard_key)

        self.stdout.write(f"{prefix}school={school_id}")
        self.stdout.write(f"{prefix}active-builders={builder_count}")
        self.stdout.write(
            f"{prefix}created={len(created)} updated={len(updated)} "
            f"skipped-existing={len(skipped)} failed=0"
        )
        if created:
            self.stdout.write(f"{prefix}created-keys={','.join(created)}")
        if updated:
            self.stdout.write(f"{prefix}updated-keys={','.join(updated)}")
        if skipped:
            self.stdout.write(f"{prefix}skipped-keys={','.join(skipped)}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}seed_all_dashboard_snapshots complete; "
                "snapshot is not live data."
            )
        )
