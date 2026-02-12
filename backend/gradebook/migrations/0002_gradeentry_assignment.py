# Generated manually on 2026-02-12
# Migration: Add FK from GradeEntry to academics.Assignment

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gradebook', '0001_initial'),
        ('academics', '0036_remove_section_teacher_id_section_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradeentry',
            name='assignment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grade_entries',
                to='academics.assignment'
            ),
        ),
    ]
