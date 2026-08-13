import uuid

import django.db.models.deletion
from django.db import migrations, models


def seed_scheduling_permissions(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    rows = {
        "scheduling.view": "View scheduling configuration and published placements",
        "scheduling.configure": "Configure scheduling sessions and academic scope",
        "scheduling.edit": "Stage or edit canonical section placements",
        "scheduling.publish": "Publish canonical section placements",
    }
    permissions = {}
    for code, description in rows.items():
        permission, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": description})
        permissions[code] = permission
    for role_code in ("HEAD_OF_SCHOOL", "REGISTRAR"):
        for permission in permissions.values():
            RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


class Migration(migrations.Migration):
    dependencies = [
        ("section_scheduler_wizard", "0002_initial"),
        ("academics", "0039_term_uniq_term_year_code"),
        ("bell_schedule_wizard", "0002_replace_stub_with_models"),
        ("room_setup_wizard", "0001_initial"),
        ("core", "0012_alter_ledgerentry_created_by_user_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionPlacement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="section_placements", to="core.academicyear")),
                ("day_template", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="section_placements", to="bell_schedule_wizard.daytemplate")),
                ("period_block", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="section_placements", to="bell_schedule_wizard.periodblock")),
                ("room", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="section_placements", to="room_setup_wizard.room")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="section_placements", to="core.school")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schedule_placements", to="academics.section")),
            ],
        ),
        migrations.AddConstraint(
            model_name="sectionplacement",
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=("section", "day_template", "period_block"), name="uniq_active_section_meeting"),
        ),
        migrations.AddConstraint(
            model_name="sectionplacement",
            constraint=models.UniqueConstraint(condition=models.Q(room__isnull=False, is_active=True), fields=("school", "academic_year", "room", "day_template", "period_block"), name="uniq_active_room_schedule_slot"),
        ),
        migrations.AddIndex(model_name="sectionplacement", index=models.Index(fields=["school", "academic_year", "is_active"], name="section_pla_school__b514dc_idx")),
        migrations.AddIndex(model_name="sectionplacement", index=models.Index(fields=["school", "day_template", "period_block"], name="section_pla_school__50cf2e_idx")),
        migrations.RunPython(seed_scheduling_permissions, migrations.RunPython.noop),
    ]