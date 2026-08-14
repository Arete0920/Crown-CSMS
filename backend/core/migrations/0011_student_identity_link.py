from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_backfill_household_family_link'),
        ('households', '0010_student_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentIdentityLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.CharField(choices=[('admissions', 'Verified admissions conversion'), ('import', 'Verified SIS import'), ('manual', 'Manual verified mapping'), ('reconciliation', 'Deterministic reconciliation')], max_length=32)),
                ('verification_status', models.CharField(choices=[('verified', 'Verified'), ('pending', 'Pending evidence')], default='verified', max_length=16)),
                ('evidence_reference', models.CharField(blank=True, default='', max_length=255)),
                ('compatibility_student', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='core_identity_link', to='households.student')),
                ('core_student', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='identity_link', to='core.student')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='student_identity_links', to='core.school')),
            ],
            options={
                'ordering': ['school_id', 'core_student_id'],
                'indexes': [models.Index(fields=['school', 'verification_status'], name='core_studen_school__8a4406_idx')],
            },
        ),
    ]
