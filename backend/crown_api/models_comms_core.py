from django.db import models

from core.models import BaseModel
from crown_api.models_households import Household, Person, Student


class MessageThread(BaseModel):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="threads",
    )
    student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="threads",
    )
    subject = models.CharField(max_length=120, blank=True, default="")
    thread_type = models.CharField(max_length=24, default="GENERAL")
    created_by = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="threads_created",
    )
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["household", "student", "last_message_at"]),
        ]
        ordering = ["-last_message_at", "-updated_at"]

    def __str__(self) -> str:
        label = self.subject or self.thread_type
        return f"{label} ({self.household})".strip()


class Message(BaseModel):
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_person = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages_sent",
    )
    body = models.TextField()
    sent_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["thread", "sent_at"]),
        ]
        ordering = ["sent_at", "created_at"]

    def __str__(self) -> str:
        return f"Message({self.thread_id}, {self.sent_at})"
