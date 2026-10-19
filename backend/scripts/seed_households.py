"""Explicitly local, fictional household seed for legacy proof only.

The legacy crown_api models have no canonical school tenant key. This script
therefore rejects hosted and non-isolated databases and never imports live data.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def run() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    import django
    django.setup()

    from django.core.management.base import CommandError
    from django.db import transaction
    from crown_api.models import Household, HouseholdMember, Person
    from crown_api.models_households import (
        ROLE_AUTHORIZED_PICKUP,
        ROLE_EMERGENCY_CONTACT,
        ROLE_FINANCIALLY_RESPONSIBLE,
        ROLE_GUARDIAN,
        ROLE_PRIMARY_GUARDIAN,
    )
    from core.legacy_demo_seed_safety import (
        LEGACY_HOUSEHOLDS,
        require_isolated_fixture_directory,
        require_local_legacy_fixture_seed,
    )

    require_local_legacy_fixture_seed("seed_households")
    with transaction.atomic():
        require_isolated_fixture_directory(Household, Person)

        for scenario in LEGACY_HOUSEHOLDS:
            household, created = Household.objects.get_or_create(
                household_name=scenario.name,
                defaults={
                    "primary_city": scenario.city,
                    "primary_state": scenario.state,
                },
            )
            if not created and (
                household.primary_city != scenario.city
                or household.primary_state != scenario.state
            ):
                raise CommandError(
                    "Existing legacy demo household does not match the fictional scenario"
                )

            for guardian, roles in (
                (
                    scenario.primary,
                    (ROLE_PRIMARY_GUARDIAN, ROLE_FINANCIALLY_RESPONSIBLE),
                ),
                (
                    scenario.secondary,
                    (
                        ROLE_GUARDIAN,
                        ROLE_EMERGENCY_CONTACT,
                        ROLE_AUTHORIZED_PICKUP,
                    ),
                ),
            ):
                person, person_created = Person.objects.get_or_create(
                    email=guardian.email,
                    defaults={
                        "first_name": guardian.first_name,
                        "last_name": guardian.last_name,
                        "phone": guardian.phone,
                    },
                )
                if not person_created and (
                    person.first_name != guardian.first_name
                    or person.last_name != guardian.last_name
                    or person.phone != guardian.phone
                ):
                    raise CommandError(
                        "Existing legacy demo contact does not match the fictional scenario"
                    )
                for role in roles:
                    HouseholdMember.objects.get_or_create(
                        household=household,
                        person=person,
                        role=role,
                        defaults={"is_primary": role == ROLE_PRIMARY_GUARDIAN},
                    )

            logger.info("Seeded fictional household %s", scenario.name)


if __name__ == "__main__":
    run()
