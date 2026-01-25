from django.db import models

from core.models import BaseModel
from crown_api.models_households import Student


class StudentProfile(BaseModel):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    student_number = models.CharField(max_length=32, unique=True, db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expected_grad_year = models.IntegerField(null=True, blank=True)
    notes_public = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["student_number"]

    def __str__(self) -> str:
        return f"{self.student_number} ({self.student})"
