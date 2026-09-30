import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0016_seed_extended_care_edit_permission"),
        ("applications", "0011_application_checklist_access_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketingCampaign",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=180)),
                ("campaign_type", models.CharField(choices=[("capacity_growth", "Capacity Growth"), ("referral", "Referral"), ("church", "Church Outreach"), ("feeder", "Preschool / Feeder"), ("general", "General Enrollment")], default="general", max_length=32)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active"), ("paused", "Paused"), ("complete", "Complete")], db_index=True, default="draft", max_length=20)),
                ("target_grade_code", models.CharField(blank=True, default="", max_length=3)),
                ("enrollment_goal", models.PositiveIntegerField(default=0)),
                ("budget_cents", models.PositiveBigIntegerField(default=0)),
                ("actual_spend_cents", models.PositiveBigIntegerField(default=0)),
                ("tuition_per_student_cents", models.PositiveBigIntegerField(default=0)),
                ("minimum_net_tuition_cents", models.PositiveBigIntegerField(default=0)),
                ("expected_retention_years", models.PositiveSmallIntegerField(default=1)),
                ("target_segment", models.JSONField(blank=True, default=dict)),
                ("portrait_domain_ids", models.JSONField(blank=True, default=list)),
                ("aid_strategy", models.JSONField(blank=True, default=dict)),
                ("created_by_user_id", models.UUIDField(blank=True, null=True)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_year", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="marketing_campaigns", to="core.academicyear")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marketing_campaigns", to="core.school")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="MarketingLead",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("stage", models.CharField(choices=[("inquiry", "Inquiry"), ("tour_scheduled", "Tour Scheduled"), ("application_started", "Application Started"), ("application_submitted", "Application Submitted"), ("accepted", "Accepted"), ("enrolled", "Enrolled"), ("lost", "Lost")], db_index=True, default="inquiry", max_length=32)),
                ("first_source", models.CharField(blank=True, default="", max_length=80)),
                ("primary_source", models.CharField(blank=True, default="", max_length=80)),
                ("conversion_source", models.CharField(blank=True, default="", max_length=80)),
                ("referral_type", models.CharField(blank=True, default="", max_length=40)),
                ("referral_detail", models.CharField(blank=True, default="", max_length=180)),
                ("assigned_to_user_id", models.UUIDField(blank=True, null=True)),
                ("last_touch_at", models.DateTimeField(blank=True, null=True)),
                ("next_follow_up_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="marketing_leads", to="applications.application")),
                ("campaign", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="crm_marketing.marketingcampaign")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marketing_leads", to="core.school")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="CampaignTouchpoint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("channel", models.CharField(choices=[("email", "Email"), ("phone", "Phone"), ("sms", "SMS"), ("event", "Event"), ("tour", "Tour"), ("referral", "Referral"), ("church", "Church"), ("system", "System")], max_length=24)),
                ("summary", models.CharField(max_length=240)),
                ("outcome", models.CharField(blank=True, default="", max_length=120)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField()),
                ("created_by_user_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("campaign", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="touchpoints", to="crm_marketing.marketingcampaign")),
                ("lead", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="touchpoints", to="crm_marketing.marketinglead")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marketing_touchpoints", to="core.school")),
            ],
            options={"ordering": ["-occurred_at"]},
        ),
        migrations.AddIndex(model_name="marketingcampaign", index=models.Index(fields=["school", "status"], name="crm_marketi_school__42f519_idx")),
        migrations.AddIndex(model_name="marketingcampaign", index=models.Index(fields=["school", "target_grade_code"], name="crm_marketi_school__f2cd43_idx")),
        migrations.AddIndex(model_name="marketinglead", index=models.Index(fields=["school", "stage"], name="crm_marketi_school__9dcc2e_idx")),
        migrations.AddIndex(model_name="marketinglead", index=models.Index(fields=["school", "campaign", "stage"], name="crm_marketi_school__1a6d21_idx")),
        migrations.AddIndex(model_name="campaigntouchpoint", index=models.Index(fields=["school", "occurred_at"], name="crm_marketi_school__d01c5f_idx")),
        migrations.AddIndex(model_name="campaigntouchpoint", index=models.Index(fields=["campaign", "occurred_at"], name="crm_marketi_campaig_373552_idx")),
    ]
