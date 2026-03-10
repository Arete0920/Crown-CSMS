from django.core.management.base import BaseCommand

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
        school_id = str(options['school_id']).strip()

        attendance_payload = attendance_sample_payload(school_id)
        attendance_payload['meta']['served_from'] = 'seed-command'
        attendance_payload['meta']['certification_candidate'] = 'hybrid'

        DashboardSnapshot.objects.update_or_create(
            school_id=school_id,
            dashboard_key='attendance',
            defaults={
                'payload': attendance_payload,
                'source': 'seed',
                'notes': 'Seeded attendance reference snapshot.',
            },
        )

        release_payload = release_reliability_sample_payload('platform')
        release_payload['meta']['served_from'] = 'seed-command'
        release_payload['meta']['certification_candidate'] = 'hybrid'

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
