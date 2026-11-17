import json
from django.core.management.base import BaseCommand
from sandbox_demo.universal_jireh import prepare_presenter_jireh


class Command(BaseCommand):
    help = "Preflight or explicitly stage fictional Jireh in the owned LOCAL presenter."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        from sandbox_demo.universal_demo import require_local_presenter
        require_local_presenter()
        self.stdout.write(json.dumps(prepare_presenter_jireh(apply=options["apply"]), sort_keys=True))
