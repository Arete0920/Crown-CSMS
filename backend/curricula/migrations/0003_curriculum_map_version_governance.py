import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_initial_versions(apps, schema_editor):
    CurriculumMap = apps.get_model("curricula", "CurriculumMap")
    CurriculumMapVersion = apps.get_model("curricula", "CurriculumMapVersion")
    CurriculumMapVersionEvent = apps.get_model("curricula", "CurriculumMapVersionEvent")
    Unit = apps.get_model("curricula", "Unit")

    for curriculum_map in CurriculumMap.objects.all().iterator():
        initial_status = "published" if curriculum_map.active else "retired"
        version = CurriculumMapVersion.objects.create(
            school_id=curriculum_map.school_id,
            curriculum_map_id=curriculum_map.id,
            version_number=1,
            status=initial_status,
            change_summary="Initial governed version created from pre-versioned curriculum map.",
        )
        CurriculumMapVersionEvent.objects.create(
            school_id=curriculum_map.school_id,
            version_id=version.id,
            from_status="",
            to_status=initial_status,
            actor_id=None,
            notes="Initial governance event created while migrating pre-versioned curriculum data.",
        )
        Unit.objects.filter(
            school_id=curriculum_map.school_id,
            curriculum_map_id=curriculum_map.id,
        ).update(curriculum_version_id=version.id)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("curricula", "0002_curriculummap_grade_band_curriculummap_subject_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CurriculumMapVersion",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("version_number", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("draft", "Draft"), ("review", "In review"), ("approved", "Approved"), ("published", "Published"), ("retired", "Retired")], db_index=True, default="draft", max_length=16)),
                ("change_summary", models.TextField(blank=True, default="")),
                ("effective_from", models.DateField(blank=True, null=True)),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("retired_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="curriculum_versions_approved", to=settings.AUTH_USER_MODEL)),
                ("curriculum_map", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="curricula.curriculummap")),
                ("submitted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="curriculum_versions_submitted", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "curriculum_map_version", "ordering": ["curriculum_map_id", "-version_number"]},
        ),
        migrations.CreateModel(
            name="CurriculumMapVersionEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("from_status", models.CharField(blank=True, default="", max_length=16)),
                ("to_status", models.CharField(max_length=16)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="curriculum_version_events", to=settings.AUTH_USER_MODEL)),
                ("version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="curricula.curriculummapversion")),
            ],
            options={"db_table": "curriculum_map_version_event", "ordering": ["created_at", "id"]},
        ),
        migrations.AddConstraint(model_name="curriculummapversion", constraint=models.UniqueConstraint(fields=("curriculum_map", "version_number"), name="uniq_curriculum_map_version_number")),
        migrations.AddConstraint(model_name="curriculummapversion", constraint=models.UniqueConstraint(condition=models.Q(("status", "published")), fields=("curriculum_map",), name="uniq_published_curriculum_map_version")),
        migrations.AddIndex(model_name="curriculummapversion", index=models.Index(fields=["school_id", "curriculum_map", "status"], name="curr_ver_school_map_status_idx")),
        migrations.AddIndex(model_name="curriculummapversion", index=models.Index(fields=["school_id", "status"], name="curr_ver_school_status_idx")),
        migrations.AddIndex(model_name="curriculummapversionevent", index=models.Index(fields=["school_id", "version", "created_at"], name="curr_evt_sch_ver_created")),
        migrations.AddField(model_name="unit", name="curriculum_version", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="units", to="curricula.curriculummapversion")),
        migrations.RunPython(create_initial_versions, migrations.RunPython.noop),
        migrations.AlterField(model_name="unit", name="curriculum_version", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="units", to="curricula.curriculummapversion")),
        migrations.AddIndex(model_name="unit", index=models.Index(fields=["school_id", "curriculum_version", "sequence"], name="curr_unit_school_ver_seq_idx")),
    ]
