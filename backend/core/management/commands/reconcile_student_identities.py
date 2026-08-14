import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from core.models import School, Student, StudentIdentityLink
from households.models import Student as CompatibilityStudent


class Command(BaseCommand):
    help = (
        'Read-only student identity reconciliation report. '
        'This command never creates, updates, or guesses identity mappings.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--school-id', dest='school_id')
        parser.add_argument('--pretty', action='store_true')

    def handle(self, *args, **options):
        schools = School.objects.order_by('id')
        school_id = options.get('school_id')
        if school_id:
            schools = schools.filter(id=school_id)
            if not schools.exists():
                raise CommandError(f'Unknown school id: {school_id}')

        report = {
            'mode': 'read_only',
            'candidate_matching': 'disabled_no_safe_deterministic_key',
            'schools': [],
        }

        for school in schools:
            core_students = Student.objects.filter(school=school)
            compatibility_students = CompatibilityStudent.objects.filter(school_id=school.id)
            links = StudentIdentityLink.objects.filter(school=school)

            mapped_core_ids = links.values_list('core_student_id', flat=True)
            mapped_compatibility_ids = links.values_list('compatibility_student_id', flat=True)

            invalid_links = links.exclude(core_student__school_id=F('school_id')).count()
            invalid_links += links.exclude(compatibility_student__school_id=F('school_id')).count()

            report['schools'].append(
                {
                    'school_id': str(school.id),
                    'school_name': school.name,
                    'core_total': core_students.count(),
                    'compatibility_total': compatibility_students.count(),
                    'mapped_total': links.count(),
                    'verified_total': links.filter(
                        verification_status=StudentIdentityLink.STATUS_VERIFIED
                    ).count(),
                    'pending_total': links.filter(
                        verification_status=StudentIdentityLink.STATUS_PENDING
                    ).count(),
                    'unmatched_core': core_students.exclude(id__in=mapped_core_ids).count(),
                    'unmatched_compatibility': compatibility_students.exclude(
                        id__in=mapped_compatibility_ids
                    ).count(),
                    'invalid_cross_tenant_links': invalid_links,
                    'ambiguous_candidates': 'not_inferred',
                }
            )

        output = json.dumps(report, indent=2 if options.get('pretty') else None, sort_keys=True)
        self.stdout.write(output)
