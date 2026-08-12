from django.core.management.base import BaseCommand, CommandError

from core.models import School
from payments.final_hardening_audit import audit_finance_hardening


class Command(BaseCommand):
    help = "Run strict Finance final-hardening invariants for one school/demo data set."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument("--school-id", dest="school_id")
        target.add_argument("--school-name", dest="school_name")

    def handle(self, *args, **options):
        school_id = options.get("school_id")
        school_name = (options.get("school_name") or "").strip()
        if school_name:
            matches = School.objects.filter(name__iexact=school_name)
            if matches.count() != 1:
                raise CommandError(
                    f"Expected exactly one school named {school_name!r}; found {matches.count()}."
                )
            school_id = matches.get().pk

        result = audit_finance_hardening(school_id=school_id)
        self.stdout.write(
            f"school_id={school_id} "
            f"checked_payments={result.checked_payments} "
            f"checked_journal_entries={result.checked_journal_entries} "
            f"checked_finance_allocations={result.checked_finance_allocations} "
            f"checked_ledger_allocations={result.checked_ledger_allocations} "
            f"checked_trace_links={result.checked_trace_links} "
            f"findings={len(result.findings)}"
        )
        for finding in result.findings:
            self.stdout.write(f"FINDING {finding}")

        if result.findings:
            raise CommandError(
                "Finance final-hardening audit failed; certification is not safe."
            )
        self.stdout.write(self.style.SUCCESS("Finance final-hardening audit PASS"))
