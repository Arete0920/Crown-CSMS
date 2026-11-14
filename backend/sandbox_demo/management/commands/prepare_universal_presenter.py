import json

from django.core.management.base import BaseCommand
from sandbox_demo.universal_demo import prepare_presenter


class Command(BaseCommand):
    help = "Preflight or explicitly create/reset the isolated LOCAL fictional presenter foundation."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(prepare_presenter(
            apply=options["apply"], reset=options["reset"],
        ), sort_keys=True))
