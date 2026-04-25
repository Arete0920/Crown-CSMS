# Generated migration for MessageTemplate

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('comms_wizard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('system', 'System Template'), ('user-generated', 'User-Generated Template')], default='system', max_length=32)),
                ('subject', models.CharField(default='', max_length=255)),
                ('body', models.TextField(default='')),
                ('variables', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_templates_created', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='message_templates', to='core.school')),
            ],
            options={
                'app_label': 'comms_wizard',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='messagetemplate',
            index=models.Index(fields=['school', 'category'], name='comms_wizar_school__idx1'),
        ),
        migrations.AddIndex(
            model_name='messagetemplate',
            index=models.Index(fields=['category', 'created_at'], name='comms_wizar_categor_idx2'),
        ),
    ]
