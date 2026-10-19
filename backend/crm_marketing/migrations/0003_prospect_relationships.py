# Additive CRM prospect records. No existing family or lead rows are modified.
import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("crm_marketing", "0002_inquiry_capture"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProspectContact",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("display_name", models.CharField(max_length=160)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("phone", models.CharField(blank=True, default="", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_prospect_contacts", to="core.school")),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.CreateModel(
            name="ProspectGroup",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("label", models.CharField(max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prospect_groups", to="crm_marketing.marketinglead")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_prospect_groups", to="core.school")),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.CreateModel(
            name="ProspectGroupMember",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("prospective_parent", "Prospective parent"), ("other_adult", "Other adult"), ("contact", "Contact")], default="contact", max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("contact", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="group_memberships", to="crm_marketing.prospectcontact")),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="members", to="crm_marketing.prospectgroup")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_prospect_group_members", to="core.school")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="EnrollmentInterest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("learner_number", models.PositiveSmallIntegerField(default=1)),
                ("grade_interest", models.CharField(max_length=16)),
                ("entry_year", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_enrollment_interests", to="applications.application")),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollment_interests", to="crm_marketing.prospectgroup")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_enrollment_interests", to="core.school")),
            ],
            options={"ordering": ["entry_year", "learner_number", "id"]},
        ),
        migrations.AddIndex(model_name="prospectcontact", index=models.Index(fields=["school", "email"], name="crm_pc_school_email_idx")),
        migrations.AddIndex(model_name="prospectgroup", index=models.Index(fields=["school", "created_at"], name="crm_pg_school_created_idx")),
        migrations.AddIndex(model_name="prospectgroupmember", index=models.Index(fields=["school", "group"], name="crm_pgm_school_group_idx")),
        migrations.AddIndex(model_name="enrollmentinterest", index=models.Index(fields=["school", "entry_year"], name="crm_ei_school_year_idx")),
        migrations.AddIndex(model_name="enrollmentinterest", index=models.Index(fields=["school", "group"], name="crm_ei_school_group_idx")),
        migrations.AddConstraint(model_name="prospectgroup", constraint=models.UniqueConstraint(condition=models.Q(lead__isnull=False), fields=("school", "lead"), name="crm_pg_unique_school_lead")),
        migrations.AddConstraint(model_name="prospectgroupmember", constraint=models.UniqueConstraint(fields=("group", "contact"), name="crm_pgm_unique_group_contact")),
        migrations.AddConstraint(model_name="enrollmentinterest", constraint=models.UniqueConstraint(fields=("group", "learner_number", "entry_year"), name="crm_ei_unique_learner_year")),
        migrations.AddConstraint(model_name="enrollmentinterest", constraint=models.UniqueConstraint(condition=models.Q(application__isnull=False), fields=("school", "application"), name="crm_ei_unique_application")),
    ]
