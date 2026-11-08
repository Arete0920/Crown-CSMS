"""Additive teacher-evaluation observation records; no live permissions enabled."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0022_diadem_configuration_permission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TeacherEvaluationCycle",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=160)),
                ("state", models.CharField(choices=[("active", "Active")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.academicyear")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
                ("staff", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="evaluation_cycles", to="core.staff")),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.CreateModel(
            name="TeacherEvaluationAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teacher_evaluation_assignments_made", to=settings.AUTH_USER_MODEL)),
                ("cycle", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="assignment", to="teacher_evaluations.teacherevaluationcycle")),
                ("evaluator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assigned_teacher_evaluations", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
            ],
        ),
        migrations.CreateModel(
            name="TeacherObservation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("observed_at", models.DateTimeField()),
                ("narrative", models.TextField(max_length=8000)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("submitted", "Submitted")], default="draft", max_length=16)),
                ("version", models.PositiveIntegerField(default=1)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cycle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="observations", to="teacher_evaluations.teacherevaluationcycle")),
                ("evaluator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
            ],
            options={"ordering": ["-observed_at", "id"]},
        ),
        migrations.CreateModel(
            name="TeacherObservationResponse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("choice", models.CharField(choices=[("acknowledged_receipt", "Acknowledged receipt"), ("disputed", "Disputed")], max_length=24)),
                ("comment", models.TextField(blank=True, default="", max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("observation", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="teacher_response", to="teacher_evaluations.teacherobservation")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
                ("teacher", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="TeacherEvaluationEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(max_length=32)),
                ("request_key", models.UUIDField()),
                ("fingerprint", models.CharField(max_length=64)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("cycle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events", to="teacher_evaluations.teacherevaluationcycle")),
                ("observation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="events", to="teacher_evaluations.teacherobservation")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.school")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddIndex(
            model_name="teacherevaluationcycle",
            index=models.Index(fields=["school", "staff", "academic_year"], name="te_cycle_scope_idx"),
        ),
        migrations.AddConstraint(
            model_name="teacherevaluationcycle",
            constraint=models.UniqueConstraint(fields=("school", "staff", "academic_year"), name="te_cycle_staff_year_once"),
        ),
        migrations.AddIndex(
            model_name="teacherobservation",
            index=models.Index(fields=["school", "cycle", "status"], name="te_observation_scope_idx"),
        ),
        migrations.AddIndex(
            model_name="teacherevaluationevent",
            index=models.Index(fields=["school", "cycle", "created_at"], name="te_event_scope_idx"),
        ),
        migrations.AddConstraint(
            model_name="teacherevaluationevent",
            constraint=models.UniqueConstraint(fields=("school", "actor", "request_key"), name="te_event_actor_retry"),
        ),
    ]
