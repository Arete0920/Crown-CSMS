"""Explicit, single-school provisioning execution; never a background scheduler."""
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from platform_ops.models import ProvisioningJob
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

        if connection.vendor != "postgresql":
            raise CommandError(
                "Execution requires PostgreSQL row-lock guarantees."
            )
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
