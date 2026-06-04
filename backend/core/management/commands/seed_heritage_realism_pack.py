from __future__ import annotations
import importlib
import os
import sys
from pathlib import Path

from django.core.management import BaseCommand, call_command


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
            """Import and run a script module from backend/scripts/"""
            # Add backend/scripts to path if not already there
            repo_root = Path(__file__).resolve().parents[4]  # Crown2026/
            scripts_dir = repo_root / "backend" / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            # Import the module and call its run() function
            try:
                mod = importlib.import_module(module_name.removesuffix(".py"))
                run = getattr(mod, "run", None)
                if not callable(run):
                    raise RuntimeError(f"{module_name} does not expose a callable run()")
                run()
            except Exception as e:
                raise RuntimeError(f"Failed to run {module_name}: {e}") from e

        self.stdout.write("=== Heritage Realism Pack Seed (canonical) ===")

        # 1) Core school + baseline objects
        call_command("seed_demo_school")
        
        # Get the school and year IDs created by seed_demo_school
        from core.models import School, AcademicYear
        school = School.objects.filter(name="Crown Demo Christian Academy").order_by("-created_at", "id").first()
        if not school:
            raise RuntimeError("No demo school found after seed_demo_school")
        year = AcademicYear.objects.filter(school=school, is_current=True).first()
        if not year:
            raise RuntimeError(f"No current academic year found for school {school.id}")
        
        self.stdout.write(f"Using school_id={school.id}, year_id={year.id}")
        
        # 2) Admissions
        call_command("seed_admissions_demo", school_id=str(school.id), year_id=str(year.id))

        # 2) Real households + guardians (scripts)
        run_script_module("seed_households.py")

        # 3) Scheduling/sections first so academics and gradebook attach cleanly
        run_script_module("seed_scheduling.py")

        # 4) Academics + curricula
        call_command("seed_academics_demo", school_id=str(school.id))
        call_command("seed_curricula_demo", school_id=str(school.id))

        # 4.5) Curriculum (Crown differentiator: mission-driven courses, units, lessons)
        from scripts.seed_curriculum_demo import seed_curriculum_demo
        curriculum_result = seed_curriculum_demo(school_id=str(school.id))
        self.stdout.write(f"Curriculum seeded: {curriculum_result['courses']} courses, {curriculum_result['units']} units, {curriculum_result['lessons']} lessons")

        # 5) Gradebook + category weights (makes the UI look alive)
        call_command("seed_gradebook_demo", school_id=str(school.id))
        call_command("seed_category_weights", school_id=str(school.id))

        # 5.5) Attendance (deterministic week for demo realism)
        call_command("seed_attendance_demo", school_id=str(school.id))

        # 6) Billing + payments
        call_command("seed_billing_demo", school_id=str(school.id))

        # 7) Finance realism scripts (optional)
        if not opts["no_finance_scripts"]:
            run_script_module("seed_finance.py")

        # 8) Communications threads (optional, but this is a demo differentiator)
        if not opts["no_comms"]:
            run_script_module("seed_comms.py")

        # 9) Ensure deterministic demo logins (skip if CROWN_DEMO_PASSWORD not set)
        demo_pw = os.environ.get("CROWN_DEMO_PASSWORD")
        if demo_pw:
            call_command("reset_demo_passwords")
        else:
            self.stdout.write(self.style.WARNING(
                "CROWN_DEMO_PASSWORD not set; skipping reset_demo_passwords (demo logins unchanged)."
            ))

        self.stdout.write(self.style.SUCCESS("Heritage realism pack: OK"))
