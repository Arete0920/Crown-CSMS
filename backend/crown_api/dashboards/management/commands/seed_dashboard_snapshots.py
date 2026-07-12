from django.core.management.base import BaseCommand, CommandError

from crown_api.dashboards.models import DashboardSnapshot
from crown_api.dashboards.sample_payloads import (
    attendance_sample_payload,
    release_reliability_sample_payload,
)


class Command(BaseCommand):
    help = 'Seed dashboard snapshot records for attendance and release reliability.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            dest='school_id',
            default='heritage-demo',
            help='School identifier for school-scoped dashboard snapshots.',
        )

    def handle(self, *args, **options):
        raw_school_id = options.get('school_id')
        school_id = '' if raw_school_id is None else str(raw_school_id).strip()
        if not school_id:
            raise CommandError('--school-id must be a non-empty school identifier.')

        attendance_payload = attendance_sample_payload(school_id)
        attendance_payload['meta']['served_from'] = 'seed-command'
        attendance_payload['meta']['live_certified'] = False
        attendance_payload['meta']['provenance'] = 'snapshot'
        attendance_payload['meta']['non_live_reason'] = 'seeded_snapshot'
        attendance_payload['meta'].pop('certification_candidate', None)

        DashboardSnapshot.objects.update_or_create(
            school_id=school_id,
            dashboard_key='attendance',
            defaults={
                'payload': attendance_payload,
                'source': 'seed',
                'notes': 'Seeded attendance reference snapshot.',
            },
        )

        release_payload = release_reliability_sample_payload(school_id)
        release_payload['meta']['served_from'] = 'seed-command'
        release_payload['meta']['live_certified'] = False
        release_payload['meta']['provenance'] = 'snapshot'
        release_payload['meta']['non_live_reason'] = 'seeded_snapshot'
        release_payload['meta'].pop('certification_candidate', None)

        DashboardSnapshot.objects.update_or_create(
            school_id=school_id,
            dashboard_key='release-reliability',
            defaults={
                'payload': release_payload,
                'source': 'seed',
                'notes': 'Seeded release reliability reference snapshot.',
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded dashboard snapshots for school_id="{school_id}".'
        ))
