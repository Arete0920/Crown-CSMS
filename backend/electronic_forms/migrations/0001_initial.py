import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0018_student_health_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ElectronicFormTemplate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.CharField(max_length=100)),
                ("version", models.PositiveIntegerField(default=1)),
                ("name", models.CharField(max_length=200)),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("form_schema", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_form_templates_created", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_form_templates", to="core.school")),
            ],
            options={"ordering": ["school_id", "key", "-version"]},
        ),
        migrations.CreateModel(
            name="ElectronicEnvelope",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("template_key", models.CharField(max_length=100)),
                ("template_version", models.PositiveIntegerField()),
                ("title", models.CharField(max_length=255)),
                ("subject_type", models.CharField(blank=True, default="", max_length=100)),
                ("subject_id", models.CharField(blank=True, default="", max_length=128)),
                ("document_snapshot", models.JSONField(default=dict)),
                ("document_sha256", models.CharField(db_index=True, max_length=64)),
                ("provider_code", models.CharField(default="crown_native", max_length=64)),
                ("external_reference", models.CharField(blank=True, default="", max_length=255)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SENT", "Sent"), ("COMPLETED", "Completed"), ("VOID", "Void")], db_index=True, default="DRAFT", max_length=20)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_envelopes_created", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_envelopes", to="core.school")),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="envelopes", to="electronic_forms.electronicformtemplate")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ElectronicSigner",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role_label", models.CharField(blank=True, default="", max_length=100)),
                ("display_name", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("signing_order", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("CONSENTED", "Consented"), ("SIGNED", "Signed"), ("DECLINED", "Declined"), ("WITHDRAWN", "Electronic consent withdrawn"), ("PAPER_REQUESTED", "Paper copy requested")], db_index=True, default="PENDING", max_length=24)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("envelope", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="signers", to="electronic_forms.electronicenvelope")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_signers", to="core.school")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_signature_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["signing_order", "created_at"]},
        ),
        migrations.CreateModel(
            name="ElectronicSignatureEvidence",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(choices=[("CONSENT", "Consent to electronic records"), ("WITHDRAW_CONSENT", "Withdraw electronic consent"), ("PAPER_COPY_REQUEST", "Request paper copy"), ("SIGN", "Sign"), ("DECLINE", "Decline")], db_index=True, max_length=32)),
                ("document_sha256", models.CharField(db_index=True, max_length=64)),
                ("signed_name", models.CharField(blank=True, default="", max_length=255)),
                ("intent_statement", models.TextField(blank=True, default="")),
                ("consent_text", models.TextField(blank=True, default="")),
                ("disclosure_version", models.CharField(blank=True, default="", max_length=64)),
                ("hardware_software_ack", models.BooleanField(default=False)),
                ("auth_method", models.CharField(default="authenticated_session", max_length=64)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, default="", max_length=512)),
                ("request_id", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("occurred_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor_user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_signature_evidence", to=settings.AUTH_USER_MODEL)),
                ("envelope", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="signature_evidence", to="electronic_forms.electronicenvelope")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="electronic_signature_evidence", to="core.school")),
                ("signer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="evidence", to="electronic_forms.electronicsigner")),
            ],
            options={"ordering": ["occurred_at", "created_at"]},
        ),
        migrations.AddConstraint(
            model_name="electronicformtemplate",
            constraint=models.UniqueConstraint(fields=("school", "key", "version"), name="uniq_eform_template_school_key_version"),
        ),
        migrations.AddIndex(
            model_name="electronicenvelope",
            index=models.Index(fields=["school", "status"], name="eform_env_school_status_idx"),
        ),
        migrations.AddIndex(
            model_name="electronicenvelope",
            index=models.Index(fields=["school", "subject_type", "subject_id"], name="eform_env_subject_idx"),
        ),
        migrations.AddConstraint(
            model_name="electronicsigner",
            constraint=models.UniqueConstraint(fields=("envelope", "user"), name="uniq_eform_envelope_user_signer"),
        ),
        migrations.AddIndex(
            model_name="electronicsignatureevidence",
            index=models.Index(fields=["school", "envelope", "action"], name="eform_evd_env_action_idx"),
        ),
        migrations.AddIndex(
            model_name="electronicsignatureevidence",
            index=models.Index(fields=["school", "actor_user", "occurred_at"], name="eform_evd_actor_time_idx"),
        ),
    ]
