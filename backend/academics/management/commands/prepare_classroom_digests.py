from django.core.management.base import BaseCommand
from academics.family_notifications import prepare_digests, prepare_conference_reminders


class Command(BaseCommand):
    help = 'Prepare deduplicated in-app family digest notices; no external delivery.'

    def handle(self, *args, **options):
        self.stdout.write(f'Prepared {prepare_digests()} digest notices and {prepare_conference_reminders()} conference reminders.')
