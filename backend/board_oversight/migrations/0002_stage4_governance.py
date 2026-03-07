# Migration for Stage 4 board governance models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board_oversight', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StrategicInitiative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('owner_role', models.CharField(max_length=100)),
                ('status', models.CharField(
                    choices=[
                        ('planning', 'Planning'),
                        ('in_progress', 'In Progress'),
                        ('complete', 'Complete'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='planning',
                    max_length=20,
                )),
                ('target_date', models.DateField(blank=True, null=True)),
                ('progress_percent', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BoardKPISnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_id', models.UUIDField(db_index=True)),
                ('month', models.DateField(db_index=True)),
                ('revenue', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('enrollment', models.IntegerField(default=0)),
                ('discipline_incidents', models.IntegerField(default=0)),
                ('financial_aid_awards', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-month'],
                'unique_together': {('school_id', 'month')},
            },
        ),
        migrations.CreateModel(
            name='RoadmapItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[
                        ('planned', 'Planned'),
                        ('in_progress', 'In Progress'),
                        ('released', 'Released'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='planned',
                    max_length=20,
                )),
                ('target_release', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['target_release', 'title']},
        ),
        migrations.CreateModel(
            name='ReleaseLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=20, unique=True)),
                ('release_date', models.DateField()),
                ('notes', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-release_date']},
        ),
    ]
