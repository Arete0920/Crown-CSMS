# backend/athletics/management/commands/seed_athletics_demo.py
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import School, Student
from athletics.models import AthleteClearance, Event, Facility, Season, Sport, Team


class Command(BaseCommand):
    help = "Seed athletics demo data for a given school (by UUID)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", type=str, required=True, help="UUID of the school.")

    def handle(self, *args, **opts):
        school = School.objects.get(id=opts["school_id"])

        basketball, _ = Sport.objects.get_or_create(
            school=school, name="Basketball", gender="Boys"
        )
        winter, _ = Season.objects.get_or_create(
            school=school,
            name="Winter 2026",
            defaults=dict(
                start_date="2026-11-01",
                end_date="2027-03-01",
                is_published=True,
            ),
        )

        team, _ = Team.objects.get_or_create(
            school=school,
            sport=basketball,
            season=winter,
            display_name="Varsity Boys Basketball",
            defaults=dict(level="V", participation_fee_cents=15000),
        )

        gym, _ = Facility.objects.get_or_create(school=school, name="Main Gym")

        # Fixed datetimes for idempotency across seed runs.
        practice_start = timezone.datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)
        practice_end = timezone.datetime(2026, 11, 10, 17, 0, tzinfo=timezone.utc)
        game_start = timezone.datetime(2026, 11, 13, 18, 0, tzinfo=timezone.utc)
        game_end = timezone.datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc)

        Event.objects.get_or_create(
            school=school,
            team=team,
            event_type="PRACTICE",
            title="Practice",
            starts_at=practice_start,
            ends_at=practice_end,
            defaults=dict(facility=gym),
        )
        Event.objects.get_or_create(
            school=school,
            team=team,
            event_type="GAME",
            title="vs. Kings Christian",
            starts_at=game_start,
            ends_at=game_end,
            defaults=dict(
                facility=gym,
                opponent="Kings Christian",
                is_home=True,
            ),
        )

        now = timezone.now()
        cleared = 0
        for s in Student.objects.filter(school=school).order_by("id")[:12]:
            c, _ = AthleteClearance.objects.get_or_create(
                student=s,
                defaults={"school_id": school.id},
            )
            c.insurance_on_file = True
            c.consent_signed_at = now
            c.physical_expires_on = (timezone.localdate() + timezone.timedelta(days=180))
            c.save()
            cleared += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded athletics demo data for {school.name}: "
            f"1 sport, 1 season, 1 team, 2 events, {cleared} clearances."
        ))
