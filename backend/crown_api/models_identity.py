from django.conf import settings
from django.db import models

from core.models import BaseModel
from crown_api.models_households import Person


class UserPersonLink(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="person_link",
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="user_links",
    )

    class Meta:
        verbose_name = "User → Person Link"
        verbose_name_plural = "User → Person Links"

    def __str__(self) -> str:
        return f"{self.user} → {self.person}"
