import json
from django.core.management.base import BaseCommand
from sandbox_demo.universal_admin import prepare_presenter_admin
from sandbox_demo.universal_demo import require_local_presenter


class Command(BaseCommand):
    help = 'Preflight or stage the existing fictional administrator workflow in the owned LOCAL presenter.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        require_local_presenter()
        self.stdout.write(json.dumps(prepare_presenter_admin(apply=options['apply']), sort_keys=True))
