from django.core.management.base import BaseCommand

from sandbox_demo.academic_seed import (
    reset_heritage_teacher_academics,
    seed_heritage_teacher_academics,
)
from sandbox_demo.admin_operations import seed_heritage_admin_context
from sandbox_demo.admissions_conversion_seed import (
    reset_heritage_admissions_conversion_scenario,
    seed_heritage_admissions_conversion_scenario,
)
from sandbox_demo.admissions_seed import (
    reset_heritage_admissions_scenario,
    seed_heritage_admissions_scenario,
)
from sandbox_demo.finance import seed_heritage_finance_context
from sandbox_demo.services import seed_heritage_flagship


class Command(BaseCommand):
    help = "Seed or reset the flagship Heritage Christian Academy demo sandbox."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear and rebuild Heritage demo data.")

    def handle(self, *args, **opts):
        reset = bool(opts.get("reset"))
        if reset:
            reset_heritage_admissions_scenario()
            reset_heritage_admissions_conversion_scenario()
            reset_heritage_teacher_academics()
        metrics = seed_heritage_flagship(reset=reset)
        metrics.update(seed_heritage_teacher_academics())
        metrics.update(seed_heritage_finance_context())
        metrics.update(seed_heritage_admissions_scenario())
        metrics.update(seed_heritage_admissions_conversion_scenario())
        metrics.update(seed_heritage_admin_context())
        for key, value in metrics.items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(self.style.SUCCESS("Heritage flagship sandbox seed complete."))
