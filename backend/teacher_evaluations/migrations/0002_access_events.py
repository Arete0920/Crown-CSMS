"""Add school-and-account-scoped, append-only evaluation access events."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teacher_evaluations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TeacherEvaluationAccessEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("permission_code", models.CharField(max_length=40, choices=[
                    ("evaluation.assign", "Assign confidential observations"),
                    ("evaluation.observe", "Observe assigned teacher"),
                    ("evaluation.read_assigned", "Read designated evaluations"),
                    ("evaluation.read_self", "Read personal submitted observations"),
                    ("evaluation.respond_self", "Respond to personal observations"),
                ])),
                ("action", models.CharField(max_length=8, choices=[("grant", "Grant"), ("revoke", "Revoke")])),
                ("reason", models.CharField(max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teacher_evaluation_access_history", to=settings.AUTH_USER_MODEL)),
                ("authorized_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teacher_evaluation_access_authorizations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="teacherevaluationaccessevent",
            index=models.Index(fields=["school", "user", "permission_code", "created_at"], name="te_access_scope_idx"),
        ),
    ]
