# backend/core/management/commands/seed_permissions.py
#
# Seeds CrownPermission codes and default RolePermission mappings.
# Safe to re-run — uses get_or_create throughout.
#
# Usage:
#   python manage.py seed_permissions
#   python manage.py seed_permissions --dry-run

from django.core.management.base import BaseCommand

from core.models import CrownPermission, RolePermission


# ──────────────────────────────────────────────────────────────────────────────
# Permission codes  (<module>.<action>)
# ──────────────────────────────────────────────────────────────────────────────
PERMISSIONS = [
    # ── core system ─────────────────────────────────────────────────────────
    ("health.view",                "View health / system-status dashboard"),
    ("director.actions",           "Execute director-level admin actions"),
    ("metrics.view",               "View all KPI dashboards"),

    # ── legacy codes kept for backwards compatibility ─────────────────────
    ("finance.edit",               "Post ledger entries, reverse transactions"),
    ("finance.period_lock",        "Lock / unlock accounting periods"),
    ("aid.view",                   "View aid applications and awards"),
    ("aid.edit",                   "Create or modify aid awards"),
    ("admissions.view",            "View admissions pipeline and applicants"),
    ("admissions.edit",            "Advance, waitlist, or deny applicants"),
    ("academics.view",             "View course enrollment, grades, attendance"),
    ("academics.edit",             "Enter grades and attendance records"),

    # ── Operations tier ──────────────────────────────────────────────────
    ("admin.view",                 "View administration dashboard"),
    ("board.view",                 "View board / governance dashboard"),
    ("finance.view",               "View financial summaries and ledger"),
    ("billing.view",               "View billing and fee dashboard"),
    ("office.view",                "View office operations dashboard"),
    ("it.view",                    "View IT / infrastructure dashboard"),
    ("facilities.view",            "View facilities dashboard"),
    ("transportation.view",        "View transportation dashboard"),

    # ── Enrollment & Revenue tier ────────────────────────────────────────
    ("financial_aid.view",         "View financial aid dashboard"),
    ("marketing.view",             "View marketing / enrollment funnel"),
    ("advancement.view",           "View advancement / fundraising dashboard"),

    # ── Academics tier ───────────────────────────────────────────────────
    ("teacher.view",               "View teacher dashboard"),
    ("registrar.view",             "View registrar dashboard"),
    ("academic_support.view",      "View SPED / academic-support dashboard"),
    ("fine_arts.view",             "View fine-arts dashboard"),
    ("library.view",               "View library dashboard"),
    ("pd.view",                    "View professional-development dashboard"),

    # ── Student & Family tier ────────────────────────────────────────────
    ("parent.view",                "View parent dashboard"),
    ("student.view",               "View student dashboard"),
    ("health.dashboard.view",      "View student health dashboard"),
    ("counseling.view",            "View counseling dashboard"),
    ("food.view",                  "View food-services dashboard"),
    ("athletics.view",             "View athletics dashboard"),
    ("spiritual_life.view",        "View spiritual-life dashboard"),
    ("extended_care.view",         "View extended-care dashboard"),
    ("communications.view",        "View communications dashboard"),
    ("student_services.view",      "View student-services dashboard"),

    # ── Safety & Integrity tier ──────────────────────────────────────────
    ("security.view",              "View security / safety dashboard"),
    ("integrity.view",             "View academic-integrity dashboard"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Default role → permission mappings
#
# role_code values must match core.models.UserRole.ROLE_CODE_CHOICES.
#   HEAD_OF_SCHOOL | AID_DIRECTOR | FINANCE_DIRECTOR | REGISTRAR
#   TEACHER | PARENT | STUDENT | SUPPORT
# ──────────────────────────────────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    "HEAD_OF_SCHOOL": [
        "health.view",
        "finance.view",
        "aid.view",
        "admissions.view",
        "academics.view",
        "metrics.view",
        "director.actions",
        "academic_support.view",
        "fine_arts.view",
        "library.view",
        "extended_care.view",
        "registrar.view",
        "communications.view",
        "pd.view",
        "student_services.view",
    ],
    "FINANCE_DIRECTOR": [
        "health.view",
        "finance.view",
        "finance.edit",
        "finance.period_lock",
        "aid.view",
        "metrics.view",
        "director.actions",
    ],
    "AID_DIRECTOR": [
        "health.view",
        "aid.view",
        "aid.edit",
        "metrics.view",
    ],
    "REGISTRAR": [
        "health.view",
        "admissions.view",
        "admissions.edit",
        "academics.view",
        "metrics.view",
        "registrar.view",
    ],
    "TEACHER": [
        "academics.view",
        "academics.edit",
    ],
    "SUPPORT": [
        "health.view",
        "metrics.view",
        "academic_support.view",
        "student_services.view",
    ],
    "PARENT": [],
    "STUDENT": [],
}


class Command(BaseCommand):
    help = "Seed CrownPermission codes and default RolePermission mappings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        tag = "[DRY RUN] " if dry_run else ""

        # ── 1. Upsert permission codes ────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING("── Permissions ──"))
        for code, description in PERMISSIONS:
            if not dry_run:
                obj, created = CrownPermission.objects.get_or_create(
                    code=code,
                    defaults={"description": description},
                )
                verb = "CREATED" if created else "EXISTS "
            else:
                verb = "WOULD CREATE"
            self.stdout.write(f"  {tag}{verb}  {code}")

        # ── 2. Upsert role → permission mappings ─────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING("── Role mappings ──"))
        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            for perm_code in permission_codes:
                if not dry_run:
                    try:
                        perm = CrownPermission.objects.get(code=perm_code)
                    except CrownPermission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  SKIP  {role_code} → {perm_code}  "
                                f"(permission not found — run without --dry-run first)"
                            )
                        )
                        continue
                    _, created = RolePermission.objects.get_or_create(
                        role_code=role_code,
                        permission=perm,
                    )
                    verb = "CREATED" if created else "EXISTS "
                else:
                    verb = "WOULD MAP"
                self.stdout.write(f"  {tag}{verb}  {role_code} → {perm_code}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete — no changes written."))
        else:
            self.stdout.write(self.style.SUCCESS("Permissions seeded successfully."))
