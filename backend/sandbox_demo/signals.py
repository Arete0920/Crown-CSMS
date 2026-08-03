"""Synthetic sandbox identity reconciliation hooks.

Only the fixed Heritage student persona is affected. Real accounts are never
linked by email or display name through this module.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import UserAccount
from crown_api.models_households import Person, Student as IdentityStudent
from crown_api.models_identity import UserPersonLink

from .catalog import DEMO_SCHOOL_ID, SANDBOX_PERSONAS


@receiver(post_save, sender=UserAccount, dispatch_uid="sandbox_demo_student_person_link")
def ensure_sandbox_student_person_link(sender, instance, **kwargs):
    persona = SANDBOX_PERSONAS["student"]
    if instance.username != persona.email:
        return
    if str(instance.school_id or "") != str(DEMO_SCHOOL_ID):
        return

    link = UserPersonLink.objects.select_related("person").filter(user=instance).first()
    if link is None:
        person = Person.objects.create(
            first_name=persona.first_name,
            last_name=persona.last_name,
            email=persona.email,
        )
        link = UserPersonLink.objects.create(user=instance, person=person)

    IdentityStudent.objects.update_or_create(
        person=link.person,
        defaults={
            "grade_level": "11",
            "active": True,
        },
    )
