import json
from django.core.management.base import BaseCommand
from sandbox_demo.universal_care import prepare_presenter_care


class Command(BaseCommand):
    help = "Preflight or stage one fictional care/Camp scenario in the owned LOCAL presenter."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(prepare_presenter_care(apply=options["apply"]), sort_keys=True))
