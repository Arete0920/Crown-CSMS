"""Seed explicitly fictional, non-custody Heritage module QA sample records."""
from django.core.management.base import BaseCommand, CommandError
from sandbox_demo.heritage_module_samples import (
    require_local_demo, seed_heritage_module_samples,
)


class Command(BaseCommand):
    help = (
        "Explicitly opt-in to local-only fictional Financial Aid, AM/PM and "
        "BLOCKED daycare sample records. Never seeds live custody approvals."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fictional-local-only", action="store_true",
            help="Confirm disposable canonical Heritage local SQLite only.",
        )

    def handle(self, *args, **options):
        if not options["fictional_local_only"]:
            raise CommandError(
                "Refusing writes without --fictional-local-only."
            )
        require_local_demo()
        results = seed_heritage_module_samples()
        for key, value in results.items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(self.style.SUCCESS(
            "Fictional local-only samples seeded; childcare readiness remains BLOCKED."
        ))
