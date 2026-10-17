"""Read-only inventory of two independent service-hour record stores.

No row-level student information, heuristic matching, or database writes.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Sum

from core.models import School
from outreach.models import ServiceLog, STATUS_APPROVED
from servicehours.models import ServiceEntry


class Command(BaseCommand):
    help = "Report school-scoped service ledger counts and totals without writes or inferred matches."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", dest="school_id")
        parser.add_argument("--pretty", action="store_true")

    def handle(self, *args, **options):
        schools = School.objects.order_by("id")
        if options.get("school_id"):
            schools = schools.filter(pk=options["school_id"])
            if not schools.exists():
                raise CommandError("Unknown school id")

        report = {
            "mode": "read_only",
            "candidate_matching": "disabled",
            "service_credit_authority": "servicehours.ServiceEntry (provisional)",
            "schools": [],
        }
        for school in schools.iterator():
            entries = ServiceEntry.objects.filter(school_id=school.pk)
            logs = ServiceLog.objects.filter(school_id=school.pk)
            approved_entries = entries.filter(status="approved")
            approved_logs = logs.filter(status=STATUS_APPROVED)
            report["schools"].append({
                "school_id": str(school.pk),
                "service_entries": entries.count(),
                "service_entries_by_status": dict(
                    entries.values_list("status").annotate(total=Count("pk"))
                ),
                "service_entries_approved_hours": str(
                    approved_entries.aggregate(total=Sum("hours"))["total"] or 0
                ),
                "outreach_logs": logs.count(),
                "outreach_logs_by_status": dict(
                    logs.values_list("status").annotate(total=Count("pk"))
                ),
                "outreach_approved_hours_separate_not_credit": str(
                    approved_logs.aggregate(total=Sum("hours"))["total"] or 0
                ),
                "outreach_approved_student_logs": approved_logs.filter(
                    participant_type="STUDENT", student_id__isnull=False
                ).count(),
                "outreach_approved_nonstudent_or_unassigned_logs": approved_logs.exclude(
                    participant_type="STUDENT", student_id__isnull=False
                ).count(),
                "linked_records": "not_implemented",
                "potential_duplicates": "not_inferred",
            })
        self.stdout.write(json.dumps(
            report, sort_keys=True, indent=2 if options.get("pretty") else None
        ))
