from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import BaseModel


ROLE_PRIMARY_GUARDIAN = "PRIMARY_GUARDIAN"
ROLE_GUARDIAN = "GUARDIAN"
ROLE_FINANCIALLY_RESPONSIBLE = "FINANCIALLY_RESPONSIBLE"
ROLE_EMERGENCY_CONTACT = "EMERGENCY_CONTACT"
ROLE_AUTHORIZED_PICKUP = "AUTHORIZED_PICKUP"

GUARDIAN_ROLES = [ROLE_PRIMARY_GUARDIAN, ROLE_GUARDIAN]


class Person(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Household(BaseModel):
    household_name = models.CharField(max_length=255)

    primary_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    primary_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    primary_city = models.CharField(max_length=100, blank=True, null=True)
    primary_state = models.CharField(max_length=2, blank=True, null=True)
    primary_postal_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ["household_name"]

    def __str__(self) -> str:
        return self.household_name


class HouseholdMember(BaseModel):
    ROLE_CHOICES = [
        (ROLE_PRIMARY_GUARDIAN, "Primary Guardian"),
        (ROLE_GUARDIAN, "Guardian"),
        (ROLE_FINANCIALLY_RESPONSIBLE, "Financially Responsible"),
        (ROLE_EMERGENCY_CONTACT, "Emergency Contact"),
        (ROLE_AUTHORIZED_PICKUP, "Authorized Pickup"),
    ]

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="members"
    )
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="household_memberships"
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "person", "role"],
                name="uniq_household_person_role",
            ),
            models.UniqueConstraint(
                fields=["household"],
                condition=Q(
                    is_primary=True,
                    role__in=GUARDIAN_ROLES,
                ),
                name="uniq_household_primary_guardian",
            ),
        ]
        ordering = ["household", "role", "person__last_name", "person__first_name"]

    def clean(self):
        super().clean()
        if self.is_primary and self.role not in set(GUARDIAN_ROLES):
            raise ValidationError({"is_primary": "Primary is only valid for guardian roles."})

    def __str__(self) -> str:
        return f"{self.household} - {self.person} ({self.role})"


class Student(BaseModel):
    person = models.OneToOneField(
        Person, on_delete=models.CASCADE, related_name="student_profile"
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="students",
    )
    grade_level = models.CharField(max_length=10)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["person__last_name", "person__first_name"]

    def __str__(self) -> str:
        return f"{self.person} (Grade {self.grade_level})"
