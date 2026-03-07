# Migration for DataDestructionCertificate in core
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_data_retention_policy'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataDestructionCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_id', models.UUIDField(db_index=True)),
                ('reference_code', models.CharField(default=uuid.uuid4, max_length=200, unique=True)),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('purged_by', models.CharField(blank=True, max_length=200)),
                ('scope_summary', models.TextField(blank=True)),
            ],
            options={'ordering': ['-issued_at']},
        ),
    ]
