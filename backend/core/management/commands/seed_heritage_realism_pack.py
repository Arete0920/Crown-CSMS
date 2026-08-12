from __future__ import annotations
import importlib
import os
import sys
from pathlib import Path

from django.core.management import BaseCommand, call_command


HERITAGE_NAME = "Heritage Christian Academy"


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

        from core.models import AcademicYear, School

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

        # 4) Scheduling/sections first so academics and gradebook attach cleanly.
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
            call_command("reset_demo_passwords")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "CROWN_DEMO_PASSWORD not set; skipping reset_demo_passwords (demo logins unchanged)."
                )
            )

        self.stdout.write(self.style.SUCCESS("Heritage realism pack: OK"))
