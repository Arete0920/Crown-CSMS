# Generated for Jireh financial-profile modernization.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aid", "0003_phase75_policy_budget_engine_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AidFinancialProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("verification_status", models.CharField(choices=[("DRAFT", "Draft"), ("SELF_ATTESTED", "Self-attested"), ("DOCUMENT_REVIEWED", "Document reviewed"), ("VERIFIED", "Verified")], default="DRAFT", max_length=24)),
                ("consent_to_reuse", models.BooleanField(default=False)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aid_financial_profiles", to="core.academicyear")),
                ("carried_forward_from", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="carried_forward_profiles", to="aid.aidfinancialprofile")),
                ("confirmed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aid_profiles_confirmed", to=settings.AUTH_USER_MODEL)),
                ("family", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aid_financial_profiles", to="core.family")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aid_financial_profiles", to="core.school")),
            ],
        ),
        migrations.CreateModel(
            name="AidHouseholdMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("ADULT", "Adult"), ("STUDENT", "Student"), ("DEPENDENT", "Dependent"), ("CONTRIBUTOR", "Financial contributor")], max_length=16)),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(blank=True, default="", max_length=100)),
                ("relationship", models.CharField(blank=True, default="", max_length=64)),
                ("lives_in_household", models.BooleanField(default=True)),
                ("financially_responsible", models.BooleanField(default=False)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="household_members", to="aid.aidfinancialprofile")),
                ("student", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aid_household_memberships", to="core.student")),
            ],
        ),
        migrations.CreateModel(
            name="AidFinancialLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.CharField(choices=[("INCOME", "Income"), ("ASSET", "Asset"), ("LIABILITY", "Liability"), ("EXPENSE", "Expense")], max_length=16)),
                ("subcategory", models.CharField(max_length=64)),
                ("label", models.CharField(blank=True, default="", max_length=160)),
                ("annual_amount_cents", models.BigIntegerField(default=0)),
                ("source_type", models.CharField(choices=[("APPLICANT", "Applicant entered"), ("PRIOR_YEAR", "Prior-year verified profile"), ("DOCUMENT", "Supporting document"), ("ADMIN", "Administrator adjustment")], default="APPLICANT", max_length=16)),
                ("source_reference", models.CharField(blank=True, default="", max_length=255)),
                ("verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="aid.aidfinancialprofile")),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aid_line_items_verified", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AidQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("key", models.SlugField(max_length=80)),
                ("prompt", models.CharField(max_length=500)),
                ("response_type", models.CharField(choices=[("TEXT", "Text"), ("NUMBER", "Number"), ("CURRENCY", "Currency"), ("BOOLEAN", "Yes/No"), ("SELECT", "Single select"), ("MULTISELECT", "Multi-select")], default="TEXT", max_length=16)),
                ("required", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("options_json", models.JSONField(blank=True, default=list)),
                ("conditions_json", models.JSONField(blank=True, default=dict)),
                ("academic_year", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aid_questions", to="core.academicyear")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aid_questions", to="core.school")),
            ],
            options={"ordering": ("display_order", "id")},
        ),
        migrations.CreateModel(
            name="AidResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("response_json", models.JSONField(blank=True, default=dict)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="custom_responses", to="aid.aidapplication")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="responses", to="aid.aidquestion")),
            ],
        ),
        migrations.AddField(
            model_name="aidapplication",
            name="financial_profile",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="aid.aidfinancialprofile"),
        ),
        migrations.AlterField(
            model_name="aidauditevent",
            name="entity_id",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name="aidauditevent",
            name="entity_type",
            field=models.CharField(choices=[("APPLICATION", "Application"), ("REVIEW", "Review"), ("AWARD", "Award"), ("PROFILE", "Financial profile")], max_length=24),
        ),
        migrations.AddConstraint(
            model_name="aidfinancialprofile",
            constraint=models.UniqueConstraint(fields=("school", "academic_year", "family"), name="aid_unique_family_financial_profile_year"),
        ),
        migrations.AddConstraint(
            model_name="aidquestion",
            constraint=models.UniqueConstraint(fields=("school", "academic_year", "key"), name="aid_unique_question_key_year"),
        ),
        migrations.AddConstraint(
            model_name="aidresponse",
            constraint=models.UniqueConstraint(fields=("application", "question"), name="aid_unique_application_question_response"),
        ),
        migrations.AddIndex(
            model_name="aidfinancialprofile",
            index=models.Index(fields=["school", "academic_year", "verification_status"], name="aid_prof_year_status_idx"),
        ),
        migrations.AddIndex(
            model_name="aidfinancialprofile",
            index=models.Index(fields=["school", "family"], name="aid_prof_school_family_idx"),
        ),
        migrations.AddIndex(
            model_name="aidhouseholdmember",
            index=models.Index(fields=["profile", "role"], name="aid_hh_profile_role_idx"),
        ),
        migrations.AddIndex(
            model_name="aidfinanciallineitem",
            index=models.Index(fields=["profile", "category"], name="aid_line_prof_cat_idx"),
        ),
        migrations.AddIndex(
            model_name="aidfinanciallineitem",
            index=models.Index(fields=["profile", "verified"], name="aid_line_prof_verified_idx"),
        ),
    ]
