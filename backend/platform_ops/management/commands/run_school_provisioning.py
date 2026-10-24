"""Explicit, single-school provisioning execution; never a background scheduler."""
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import DatabaseError

from platform_ops.models import ProvisioningJob

# An operator-provided CROWN_ENV or DATABASE_URL does not prove a DEV target.
DEV_POSTGRES_HOST = "crown-pg-dev.postgres.database.azure.com"
DEV_APP_HOST = "crown-api-dev.azurewebsites.net"


def _verify_dev_postgresql_target(db) -> None:
    """Check pinned target, session identity and verified TLS before mutation.

    The only non-Azure exception is an isolated pytest-created local database.
    It cannot connect to another Azure server or an ordinary local database.
    """
    if db.vendor != "postgresql":
        raise CommandError("Execution requires PostgreSQL row-lock guarantees.")

    config = db.settings_dict
    host = str(config.get("HOST") or "").strip().rstrip(".").lower()
    port = str(config.get("PORT") or "5432")
    name = str(config.get("NAME") or "").strip()
    is_isolated_test = bool(
        os.getenv("PYTEST_CURRENT_TEST")
        and os.getenv("DJANGO_SETTINGS_MODULE") == "crown_api.test_settings"
        and not os.getenv("WEBSITE_HOSTNAME")
        and host in {"localhost", "127.0.0.1"}
        and name.startswith("test_")
    )
    if not is_isolated_test:
        options = config.get("OPTIONS") or {}
        if (
            host != DEV_POSTGRES_HOST
            or port != "5432"
            or not name
            or name.lower() in {"postgres", "template0", "template1"}
            or os.getenv("WEBSITE_HOSTNAME", "").strip().lower() != DEV_APP_HOST
            or not isinstance(options, dict)
            or str(options.get("sslmode") or "").lower() != "verify-full"
        ):
            raise CommandError(
                "Execution requires the pinned DEV PostgreSQL target, "
                "hosted app identity, and hostname-verified TLS."
            )
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_schema(), pg_is_in_recovery()"
            )
            if cursor.fetchone() != (name, "public", False):
                raise CommandError("Connected DEV database identity does not match.")
            if not is_isolated_test:
                cursor.execute(
                    "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"
                )
                if cursor.fetchone() != (True,):
                    raise CommandError("DEV database TLS is not verified.")
    except DatabaseError as exc:
        raise CommandError("Unable to verify DEV database identity.") from exc

from platform_ops.provisioning import (
    ProvisioningAuditError,
    ProvisioningStateError,
    run_provisioning_job,
)


class Command(BaseCommand):
    help = "Inspect or explicitly execute exactly one queued school-provisioning job."

    def add_arguments(self, parser):
        parser.add_argument("--job-id", required=True, help="Exact queued job UUID")
        parser.add_argument("--actor-id", required=True, help="Active platform-superuser UUID")
        parser.add_argument(
            "--apply", action="store_true",
            help="Explicitly authorize database mutations for this job",
        )
        parser.add_argument(
            "--confirm-job-id", help="Must equal --job-id to execute",
        )

    def handle(self, *args, **options):
        try:
            job_id = uuid.UUID(options["job_id"])
            actor_id = uuid.UUID(options["actor_id"])
        except (ValueError, TypeError) as exc:
            raise CommandError("Provide valid job and actor UUIDs.") from exc

        actor = get_user_model().objects.filter(pk=actor_id).first()
        if not (
            actor and actor.is_active and actor.is_superuser
            and actor.is_authenticated
        ):
            raise CommandError("An active platform superuser is required.")

        job = ProvisioningJob.objects.filter(pk=job_id).first()
        if job is None:
            raise CommandError("Provisioning job not found.")

        if not options["apply"]:
            self.stdout.write(
                f"READ_ONLY job={job.id} state={job.state}; no changes applied"
            )
            return

        if options["confirm_job_id"] != str(job_id):
            raise CommandError("Confirm exact job UUID with --confirm-job-id.")

        # An attributed actor UUID is not proof of shell identity. Restrict
        # mutations to a specifically identified development environment;
        # never allow the management command to touch production by accident.
        labels = {
            os.getenv(key, "").strip().lower()
            for key in (
                "CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT",
                "APP_ENV", "AZURE_ENVIRONMENT",
            )
            if os.getenv(key, "").strip()
        }
        if (
            not labels
            or labels - {"dev", "development"}
            or os.getenv("CROWN_ENV", "").strip().lower() not in {
                "dev", "development"
            }
            or (
                os.getenv("WEBSITE_HOSTNAME", "")
                and not os.getenv("WEBSITE_HOSTNAME", "").split(".", 1)[0]
                .lower().endswith("-dev")
            )
        ):
            raise CommandError(
                "Execution requires an explicitly identified DEV environment."
            )

        _verify_dev_postgresql_target(connection)
        try:
            completed = run_provisioning_job(job, actor_user_id=actor.pk)
        except (ProvisioningStateError, ProvisioningAuditError) as exc:
            raise CommandError(str(exc)) from exc

        if completed.state != ProvisioningJob.STATE_SUCCEEDED:
            raise CommandError(
                f"Job {job.id} ended in {completed.state}. "
                "Activation not certified; investigate restricted logs."
            )
        self.stdout.write(
            self.style.SUCCESS(f"PROVISIONED job={job.id} state=succeeded")
        )
