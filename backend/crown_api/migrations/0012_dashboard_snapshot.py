from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crown_api', '0011_alter_sectionenrollment_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_id', models.CharField(db_index=True, max_length=64)),
                ('dashboard_key', models.SlugField(db_index=True, max_length=120)),
                ('payload', models.JSONField(default=dict)),
                ('source', models.CharField(default='manual', max_length=32)),
                ('notes', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'dashboard_snapshots',
                'ordering': ['school_id', 'dashboard_key'],
                'unique_together': {('school_id', 'dashboard_key')},
            },
        ),
        migrations.AddIndex(
            model_name='dashboardsnapshot',
            index=models.Index(fields=['school_id', 'dashboard_key'], name='dashboard_s_school__f79a6d_idx'),
        ),
    ]
