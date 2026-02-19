from django.core.management.base import BaseCommand
from core.models import School
from graduation.models import GraduationRule

class Command(BaseCommand):
    help = "Seed demo graduation rule (v1)."

    def handle(self, *args, **options):
        school = School.objects.first()
        if school is None:
            self.stdout.write(self.style.ERROR("No School found. Seed a School first."))
            return

        rule, created = GraduationRule.objects.get_or_create(
            school=school,
            is_active=True,
            defaults={
                "name": "Default Graduation Policy",
                "required_total_credits": 24.00,
                "notes": "Demo seed: v1 only enforces total credits.",
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Exists'} GraduationRule for school={school.id} required_total_credits={rule.required_total_credits}"
        ))
