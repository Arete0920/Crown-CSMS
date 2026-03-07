# Generated migration for Stage 3 onboarding models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_data_retention_policy'),
        ('onboarding', '0001_initial'),
    ]

    operations = [
        # ImportFieldMapping — generic field mapping for CSV import sessions
        migrations.CreateModel(
            name='ImportFieldMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_field', models.CharField(max_length=100)),
                ('target_model', models.CharField(max_length=100)),
                ('target_field', models.CharField(max_length=100)),
                ('import_session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='field_mappings',
                    to='onboarding.importsession',
                )),
            ],
            options={
                'ordering': ['source_field'],
            },
        ),
        # OnboardingTask — per-school setup checklist
        migrations.CreateModel(
            name='OnboardingTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(max_length=200)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('complete', 'Complete')],
                    default='pending',
                    max_length=20,
                )),
                ('order', models.IntegerField(default=0)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('school', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='onboarding_tasks',
                    to='core.school',
                )),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('school', 'task_name')},
            },
        ),
        # HelpArticle — contextual in-app help content
        migrations.CreateModel(
            name='HelpArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('content', models.TextField()),
                ('module', models.CharField(db_index=True, max_length=100)),
                ('published', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['module', 'title'],
            },
        ),
    ]
