from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from core.models import School
from core.tenant_models import tenant_context
from graduation.models import GraduationRule

class Command(BaseCommand):
    help = "Seed demo graduation rule (v1)."

    def add_arguments(self, parser):
        parser.add_argument('--school-id', help='Active school UUID; required for multi-school data.')

    def handle(self, *args, **options):
        if options.get('school_id'):
            try:
                school = School.objects.get(pk=options['school_id'], is_active=True)
            except (School.DoesNotExist, ValueError, ValidationError) as exc:
                raise CommandError('A valid active --school-id is required.') from exc
        else:
            candidates = list(School.objects.filter(is_active=True)[:2])
            if len(candidates) != 1:
                raise CommandError('Specify --school-id; school selection is missing or ambiguous.')
            school = candidates[0]
        with tenant_context(school):
            return self._seed_school(school)

    def _seed_school(self, school):
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
