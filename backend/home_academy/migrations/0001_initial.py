# Generated manually for Home Academy workpack 1.

import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HomeAcademyProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("school_id", models.IntegerField(db_index=True, unique=True)),
                ("public_program_name", models.CharField(max_length=160)),
                ("program_type", models.CharField(choices=[("support_only", "Support Only"), ("umbrella_school", "Umbrella / School of Record"), ("hybrid_academy", "Hybrid Academy"), ("supplemental_course_only", "Supplemental Course Only"), ("diploma_track", "Diploma Track")], default="support_only", max_length=40)),
                ("handbook_document_id", models.CharField(blank=True, max_length=120)),
                ("active_school_year", models.CharField(blank=True, max_length=20)),
                ("default_sports_min_academic_courses", models.PositiveSmallIntegerField(default=2)),
                ("default_activity_min_academic_courses", models.PositiveSmallIntegerField(default=1)),
                ("default_homeschool_seat_cap", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="FinancialAidRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("school_id", models.IntegerField(db_index=True)),
                ("charge_type", models.CharField(choices=[("tuition", "Tuition"), ("course_fee", "Course Fee"), ("lab_fee", "Lab Fee"), ("activity_fee", "Activity Fee"), ("athletic_fee", "Athletic Fee"), ("materials_fee", "Materials Fee"), ("uniform_fee", "Uniform Fee"), ("testing_fee", "Testing Fee"), ("transcript_fee", "Transcript Fee"), ("graduation_audit_fee", "Graduation Audit Fee"), ("diploma_fee", "Diploma Fee"), ("platform_fee", "Platform Fee")], max_length=40)),
                ("aid_eligible", models.BooleanField(default=False)),
                ("esa_eligible", models.BooleanField(default=False)),
                ("scholarship_eligible", models.BooleanField(default=False)),
                ("requires_academic_anchor", models.BooleanField(default=True)),
                ("max_award_percent", models.PositiveSmallIntegerField(default=0)),
                ("max_award_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="HomeAcademyEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("school_id", models.IntegerField(db_index=True)),
                ("student_id", models.IntegerField(db_index=True)),
                ("household_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("status", models.CharField(choices=[("standard_enrollment", "Standard Enrollment"), ("homeschool_affiliate", "Homeschool Affiliate"), ("homeschool_course_only", "Homeschool Course Only"), ("homeschool_lab_only", "Homeschool Lab Only"), ("homeschool_hybrid", "Homeschool Hybrid"), ("homeschool_school_of_record", "Homeschool School of Record"), ("homeschool_diploma_track", "Homeschool Diploma Track"), ("homeschool_support_only", "Homeschool Support Only")], default="homeschool_affiliate", max_length=50)),
                ("school_of_record_status", models.CharField(choices=[("none", "None"), ("parent_is_record", "Parent Is School of Record"), ("school_is_record", "School Is School of Record"), ("outside_school_is_record", "Outside School Is School of Record")], default="parent_is_record", max_length=40)),
                ("diploma_eligibility_status", models.CharField(choices=[("not_eligible", "Not Eligible"), ("eligible_pending", "Eligible Pending Requirements"), ("eligible_approved", "Eligible Approved"), ("not_approved", "Not Approved")], default="not_eligible", max_length=40)),
                ("grade_level", models.CharField(blank=True, max_length=20)),
                ("advisor_id", models.IntegerField(blank=True, null=True)),
                ("registrar_id", models.IntegerField(blank=True, null=True)),
                ("start_date", models.DateField(default=django.utils.timezone.now)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("program", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="home_academy.homeacademyprogram")),
            ],
        ),
        migrations.CreateModel(
            name="Offering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("school_id", models.IntegerField(db_index=True)),
                ("offering_type", models.CharField(choices=[("academic_course", "Academic Course"), ("lab", "Lab"), ("sport", "Sport"), ("music", "Music"), ("drama", "Drama"), ("art", "Art"), ("chapel", "Chapel"), ("club", "Club"), ("student_life", "Student Life"), ("event", "Event"), ("testing", "Testing"), ("transcript_review", "Transcript Review"), ("graduation_audit", "Graduation Audit"), ("dual_enrollment_support", "Dual Enrollment Support")], db_index=True, max_length=40)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("school_year", models.CharField(blank=True, max_length=20)),
                ("term", models.CharField(blank=True, max_length=40)),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ("billing_frequency", models.CharField(choices=[("one_time", "One Time"), ("monthly", "Monthly"), ("semester", "Semester"), ("season", "Season"), ("annual", "Annual"), ("per_event", "Per Event"), ("per_lesson", "Per Lesson")], default="one_time", max_length=20)),
                ("credit_bearing", models.BooleanField(default=False)),
                ("transcript_eligible", models.BooleanField(default=False)),
                ("diploma_track_eligible", models.BooleanField(default=False)),
                ("requires_academic_anchor", models.BooleanField(default=True)),
                ("min_academic_courses_required", models.PositiveSmallIntegerField(default=0)),
                ("requires_school_of_record", models.BooleanField(default=False)),
                ("requires_admin_approval", models.BooleanField(default=True)),
                ("requires_coach_or_director_approval", models.BooleanField(default=False)),
                ("blocks_if_past_due", models.BooleanField(default=True)),
                ("blocks_if_forms_missing", models.BooleanField(default=True)),
                ("total_capacity", models.PositiveIntegerField(default=0)),
                ("reserved_full_time_seats", models.PositiveIntegerField(default=0)),
                ("homeschool_seat_cap", models.PositiveIntegerField(default=0)),
                ("buffer_seats", models.PositiveIntegerField(default=0)),
                ("waitlist_enabled", models.BooleanField(default=True)),
                ("active", models.BooleanField(default=True)),
                ("staff_owner_id", models.IntegerField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("program", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="offerings", to="home_academy.homeacademyprogram")),
            ],
        ),
        migrations.CreateModel(
            name="OfferingEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("school_id", models.IntegerField(db_index=True)),
                ("student_id", models.IntegerField(db_index=True)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("pending_eligibility", "Pending Eligibility"), ("eligible", "Eligible"), ("waitlisted", "Waitlisted"), ("approved", "Approved"), ("active", "Active"), ("denied", "Denied"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="requested", max_length=40)),
                ("eligibility_status", models.CharField(default="pending", max_length=40)),
                ("eligibility_failures", models.JSONField(blank=True, default=list)),
                ("payment_status", models.CharField(choices=[("not_required", "Not Required"), ("pending", "Pending"), ("paid", "Paid"), ("past_due", "Past Due"), ("waived", "Waived")], default="pending", max_length=20)),
                ("form_status", models.CharField(choices=[("not_required", "Not Required"), ("missing", "Missing"), ("complete", "Complete")], default="missing", max_length=20)),
                ("roster_status", models.CharField(default="pending", max_length=40)),
                ("transcript_posting_status", models.CharField(default="not_applicable", max_length=40)),
                ("admin_approved", models.BooleanField(default=False)),
                ("coach_or_director_approved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("home_academy_enrollment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="offering_enrollments", to="home_academy.homeacademyenrollment")),
                ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="home_academy.offering")),
            ],
        ),
        migrations.CreateModel(
            name="TranscriptPostingRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requires_registrar_approval", models.BooleanField(default=True)),
                ("transcript_category", models.CharField(blank=True, max_length=80)),
                ("credit_value", models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ("grade_source", models.CharField(blank=True, max_length=80)),
                ("diploma_requirement_area", models.CharField(blank=True, max_length=80)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("offering", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="transcript_rule", to="home_academy.offering")),
            ],
        ),
        migrations.AddIndex(
            model_name="homeacademyprogram",
            index=models.Index(fields=["school_id", "is_active"], name="home_acade_school__d5f6b9_idx"),
        ),
        migrations.AddIndex(
            model_name="financialaidrule",
            index=models.Index(fields=["school_id", "charge_type", "active"], name="home_acade_school__0e7bb3_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="financialaidrule",
            unique_together={("school_id", "charge_type")},
        ),
        migrations.AddIndex(
            model_name="homeacademyenrollment",
            index=models.Index(fields=["school_id", "student_id", "is_active"], name="home_acade_school__69991b_idx"),
        ),
        migrations.AddIndex(
            model_name="homeacademyenrollment",
            index=models.Index(fields=["school_id", "status"], name="home_acade_school__e8dbdb_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="homeacademyenrollment",
            unique_together={("school_id", "student_id", "program")},
        ),
        migrations.AddIndex(
            model_name="offering",
            index=models.Index(fields=["school_id", "offering_type", "active"], name="home_acade_school__5dfcdd_idx"),
        ),
        migrations.AddIndex(
            model_name="offering",
            index=models.Index(fields=["school_id", "school_year", "term"], name="home_acade_school__39a9f8_idx"),
        ),
        migrations.AddIndex(
            model_name="offeringenrollment",
            index=models.Index(fields=["school_id", "student_id"], name="home_acade_school__0ca03f_idx"),
        ),
        migrations.AddIndex(
            model_name="offeringenrollment",
            index=models.Index(fields=["school_id", "status"], name="home_acade_school__295752_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="offeringenrollment",
            unique_together={("school_id", "student_id", "offering")},
        ),
    ]
