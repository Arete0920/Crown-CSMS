from __future__ import annotations
import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandError

from core.demo_seed_safety import require_local_demo_seed
from core.legacy_demo_seed_safety import require_local_legacy_fixture_seed


HERITAGE_NAME = "Heritage Christian Academy"
_SCHEDULING_ID_ENV = "CROWN_LEGACY_SCHEDULING_SCHOOL_ID"


@contextmanager
def _bound_scheduling_school_id(school_id: str):
    """Bind only the verified Heritage ID for the standalone legacy script."""
    existing = os.environ.get(_SCHEDULING_ID_ENV)
    if existing and existing != school_id:
        raise CommandError(
            "CROWN_LEGACY_SCHEDULING_SCHOOL_ID conflicts with Heritage demo school."
        )
    os.environ[_SCHEDULING_ID_ENV] = school_id
    try:
        yield
    finally:
        if existing is None:
            os.environ.pop(_SCHEDULING_ID_ENV, None)
        else:
            os.environ[_SCHEDULING_ID_ENV] = existing


class Command(BaseCommand):
    help = "Seed Heritage demo with realism pack: linked data across roles, finance, aid, comms, scheduling, academics."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-comms",
            action="store_true",
            help="Skip seeding communications threads (faster runs).",
        )
        parser.add_argument(
            "--no-finance-scripts",
            action="store_true",
            help="Skip extra finance realism scripts (faster runs).",
        )

    def handle(self, *args, **opts):
        # Fail before creating any school, family, ledger, or attendance records.
        # The later legacy household/finance scripts require this authorization;
        # discovering it after seed_demo_school would leave partial fixture data.
        require_local_demo_seed(operation="Heritage realism pack")
        require_local_legacy_fixture_seed("Heritage realism pack")

        # Both legacy scripts are intentionally local-only. Explicit opt-in is
        # required before any school or finance fixture can be created.
        if os.getenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", "").strip().lower() != "true":
            raise CommandError(
                "CROWN_ALLOW_LEGACY_SCHEDULING_SEED=true is required."
            )

        from core.models import AcademicYear, School
        from crown_api.models import Household, Person
        from core.legacy_demo_seed_safety import require_isolated_fixture_directory

        # Do not create Heritage school records and only later discover that
        # existing customer schools/households make the fixtures unsafe.
        require_isolated_fixture_directory(Household, Person)
        if School.objects.exclude(name=HERITAGE_NAME).exists():
            raise CommandError("Heritage realism pack requires a single-school database.")
        current = list(School.objects.filter(name=HERITAGE_NAME).values_list("id", flat=True))
        if len(current) > 1:
            raise CommandError("Multiple Heritage schools found; refusing legacy fixture pack.")
        supplied = os.environ.get(_SCHEDULING_ID_ENV, "").strip()
        if supplied and (not current or supplied != str(current[0])):
            raise CommandError(
                "CROWN_LEGACY_SCHEDULING_SCHOOL_ID conflicts with the existing Heritage school."
            )

        def run_script_module(module_name: str):
            """Import and run a script module from backend/scripts/."""
            repo_root = Path(__file__).resolve().parents[4]
            scripts_dir = repo_root / "backend" / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            try:
                mod = importlib.import_module(module_name.removesuffix(".py"))
                run = getattr(mod, "run", None)
                if not callable(run):
                    raise RuntimeError(f"{module_name} does not expose a callable run()")
                run()
            except Exception as e:
                raise RuntimeError(f"Failed to run {module_name}: {e}") from e

        self.stdout.write("=== Heritage Realism Pack Seed (canonical) ===")

        # 1) Core school + baseline objects. Heritage is the only demo school.
        call_command("seed_demo_school", school_name=HERITAGE_NAME)

        schools = School.objects.filter(name=HERITAGE_NAME).order_by("-created_at", "id")
        school = schools.first()
        if school is None:
            raise RuntimeError(
                "Heritage Christian Academy was not created by seed_demo_school; "
                "cannot establish the canonical single-school sandbox identity."
            )
        if schools.exclude(pk=school.pk).exists():
            raise RuntimeError(
                "Multiple Heritage Christian Academy demo-school records exist; "
                "single-school sandbox identity is unsafe."
            )

        year = AcademicYear.objects.filter(school=school, is_current=True).first()
        if not year:
            raise RuntimeError(f"No current academic year found for school {school.id}")

        self.stdout.write(
            f"Using school={HERITAGE_NAME!r}, school_id={school.id}, year_id={year.id}"
        )

        # 2) Admissions.
        call_command("seed_admissions_demo", school_id=str(school.id), year_id=str(year.id))

        # 3) Real households + guardians.
        run_script_module("seed_households.py")

        # 4) Scheduling requires explicit opt-in. The only selected tenant
        # is the verified sole Heritage school, bound for this one call.
        with _bound_scheduling_school_id(str(school.id)):
            run_script_module("seed_scheduling.py")

        # 5) Academics + curricula.
        call_command("seed_academics_demo", school_id=str(school.id))
        call_command("seed_curricula_demo", school_id=str(school.id))

        from scripts.seed_curriculum_demo import seed_curriculum_demo

        curriculum_result = seed_curriculum_demo(school_id=str(school.id))
        self.stdout.write(
            f"Curriculum seeded: {curriculum_result['courses']} courses, "
            f"{curriculum_result['units']} units, {curriculum_result['lessons']} lessons"
        )

        # 6) Gradebook + attendance.
        call_command("seed_gradebook_demo", school_id=str(school.id))
        call_command("seed_category_weights", school_id=str(school.id))
        call_command("seed_attendance_demo", school_id=str(school.id))

        # 7) Billing + payments.
        call_command("seed_billing_demo", school_id=str(school.id))

        # 8) Finance realism scripts.
        if not opts["no_finance_scripts"]:
            run_script_module("seed_finance.py")

        # 9) Communications threads.
        if not opts["no_comms"]:
            run_script_module("seed_comms.py")

        # 10) Deterministic demo logins when configured.
        demo_pw = os.environ.get("CROWN_DEMO_PASSWORD")
        if demo_pw:
            call_command("reset_demo_passwords", school_id=str(school.id))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "CROWN_DEMO_PASSWORD not set; skipping reset_demo_passwords (demo logins unchanged)."
                )
            )

        self.stdout.write(self.style.SUCCESS("Heritage realism pack: OK"))
