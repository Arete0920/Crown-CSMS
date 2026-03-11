from __future__ import annotations
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import School
from crown_api.models_comms_core import MessageThread, Message

SUBJECTS = [
    "Reminder: Quiz on Friday",
    "Field Trip Permission Slip",
    "Attendance Follow-up",
    "Tuition Question",
    "Chapel Focus This Week",
    "Missing Assignment Notice",
    "Great Progress Update",
]

BODIES = [
    "Quick reminder about the upcoming quiz. Please review notes and be prepared.",
    "Please complete the permission slip by Wednesday. Let us know if you have questions.",
    "We noticed an attendance pattern and wanted to check in. Anything we can help with?",
    "Reaching out regarding your current balance and payment plan options.",
    "This week's chapel theme is serving others. Encourage your student to participate.",
    "One assignment is currently missing. Please have it submitted by end of day tomorrow.",
    "Just a quick note: your student has shown strong improvement this week. Well done.",
]

def _set_school_fields(thread, school):
    # school FK vs school_id string
    if hasattr(thread, "school_id") and not hasattr(thread, "school"):
        thread.school_id = str(school.id)

class Command(BaseCommand):
    help = "Seed comms threads + messages for demo (school-scoped when supported)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--threads", type=int, default=12)
        parser.add_argument("--messages-per", type=int, default=4)

    def handle(self, *args, **opts):
        school = School.objects.get(pk=opts["school_id"])
        User = get_user_model()
        users = list(User.objects.all()[:50])
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Ensure CI user / demo users exist."))
            return

        created_threads = 0
        for _ in range(opts["threads"]):
            subject = random.choice(SUBJECTS)
            kwargs = {"subject": subject}
            if hasattr(MessageThread, "school"):
                kwargs["school"] = school
            elif hasattr(MessageThread, "school_id"):
                kwargs["school_id"] = str(school.id)

            t = MessageThread.objects.create(**kwargs)

            # participants if supported
            if hasattr(t, "participants"):
                try:
                    t.participants.add(*random.sample(users, k=min(2, len(users))))
                except Exception:
                    pass

            # messages
            k = opts["messages_per"]
            for i in range(k):
                sender = random.choice(users)
                Message.objects.create(
                    thread=t,
                    sender=sender,
                    body=random.choice(BODIES),
                )

            created_threads += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_threads} comms threads for {school.name}"))
