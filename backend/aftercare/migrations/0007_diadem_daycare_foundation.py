"""Standalone Diadem schema branch from aftercare 0006.

Extended Care PR #569 independently owns 0007_care_session_am_pm. If both
are accepted, add a no-op merge migration depending on both 0007 leaves.
No existing AM/PM or attendance tables are altered here.
"""
import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("aftercare","0006_align_canonical_index_names"),("households","0010_student_account"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(
            name="DaycareSite",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("code",models.SlugField(max_length=48)),
                ("name",models.CharField(max_length=160)),
                ("is_active",models.BooleanField(default=False)),
            ],
            options={"constraints":[models.UniqueConstraint(fields=["school","code"],name="dia_site_school_code_uq")],"indexes":[models.Index(fields=["school","is_active"],name="dia_site_school_active_idx")]},
        ),
        migrations.CreateModel(
            name="DaycareRoom",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("site",models.ForeignKey("aftercare.DaycareSite",on_delete=django.db.models.deletion.PROTECT,related_name="care_rooms")),
                ("code",models.SlugField(max_length=48)),
                ("name",models.CharField(max_length=160)),
                ("licensed_capacity",models.PositiveIntegerField(null=True,blank=True)),
                ("max_children_per_staff",models.PositiveIntegerField(null=True,blank=True)),
                ("policy_source",models.CharField(max_length=255,blank=True,default="")),
                ("policy_verified_by",models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,null=True,blank=True,related_name="daycare_room_policy_approvals")),
                ("policy_verified_at",models.DateTimeField(null=True,blank=True)),
                ("is_active",models.BooleanField(default=False)),
            ],
            options={"constraints":[models.UniqueConstraint(fields=["site","code"],name="dia_room_site_code_uq"),models.CheckConstraint(condition=models.Q(licensed_capacity__isnull=True)|models.Q(licensed_capacity__gt=0),name="dia_room_capacity_positive_ck"),models.CheckConstraint(condition=models.Q(max_children_per_staff__isnull=True)|models.Q(max_children_per_staff__gt=0),name="dia_room_ratio_positive_ck")],"indexes":[models.Index(fields=["school","site","is_active"],name="dia_room_school_site_idx")]},
        ),
        migrations.CreateModel(
            name="DaycareChild",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("site",models.ForeignKey("aftercare.DaycareSite",on_delete=django.db.models.deletion.PROTECT,related_name="care_children")),
                ("household",models.ForeignKey("households.Household",on_delete=django.db.models.deletion.PROTECT,related_name="daycare_children")),
                ("first_name",models.CharField(max_length=80)),
                ("last_name",models.CharField(max_length=80)),
                ("date_of_birth",models.DateField()),
                ("linked_student",models.ForeignKey("households.Student",on_delete=django.db.models.deletion.PROTECT,related_name="daycare_profiles",null=True,blank=True)),
                ("is_active",models.BooleanField(default=False)),
            ],
            options={"constraints":[],"indexes":[models.Index(fields=["school","site","is_active"],name="dia_child_school_site_idx"),models.Index(fields=["school","household"],name="dia_child_household_idx")]},
        ),
        migrations.CreateModel(
            name="DaycareGuardianAuthority",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("child",models.ForeignKey("aftercare.DaycareChild",on_delete=django.db.models.deletion.PROTECT,related_name="guardian_authorities")),
                ("guardian",models.ForeignKey("households.Guardian",on_delete=django.db.models.deletion.PROTECT,related_name="daycare_authorities")),
                ("is_active",models.BooleanField(default=False)),
                ("can_view",models.BooleanField(default=False)),
                ("can_pickup",models.BooleanField(default=False)),
                ("custody_status",models.CharField(max_length=12,choices=[("UNKNOWN","Unknown"),("CLEAR","Clear"),("RESTRICTED","Restricted")],default="UNKNOWN")),
                ("verified_by",models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,null=True,blank=True,related_name="daycare_guardian_verifications")),
                ("verified_at",models.DateTimeField(null=True,blank=True)),
                ("effective_from",models.DateTimeField(null=True,blank=True)),
                ("effective_until",models.DateTimeField(null=True,blank=True)),
            ],
            options={"constraints":[models.UniqueConstraint(fields=["child","guardian"],name="dia_guard_child_guard_uq"),models.CheckConstraint(condition=models.Q(effective_from__isnull=True)|models.Q(effective_until__isnull=True)|models.Q(effective_until__gt=models.F("effective_from")),name="dia_guard_window_order_ck")],"indexes":[models.Index(fields=["school","child","is_active"],name="dia_guard_school_child_idx")]},
        ),
        migrations.CreateModel(
            name="DaycareProgram",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("site",models.ForeignKey("aftercare.DaycareSite",on_delete=django.db.models.deletion.PROTECT,related_name="care_programs")),
                ("code",models.CharField(max_length=20,choices=[("DAYCARE","Daycare"),("PRESCHOOL","Preschool")])),
                ("name",models.CharField(max_length=160)),
                ("is_active",models.BooleanField(default=False)),
            ],
            options={"constraints":[models.UniqueConstraint(fields=["site","code"],name="dia_program_site_code_uq")],"indexes":[models.Index(fields=["school","site","is_active"],name="dia_prog_school_site_idx")]},
        ),
        migrations.CreateModel(
            name="DaycareEnrollment",
            fields=[("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
                ("site",models.ForeignKey("aftercare.DaycareSite",on_delete=django.db.models.deletion.PROTECT,related_name="care_enrollments")),
                ("child",models.ForeignKey("aftercare.DaycareChild",on_delete=django.db.models.deletion.PROTECT,related_name="care_enrollments")),
                ("program",models.ForeignKey("aftercare.DaycareProgram",on_delete=django.db.models.deletion.PROTECT,related_name="care_enrollments")),
                ("room",models.ForeignKey("aftercare.DaycareRoom",on_delete=django.db.models.deletion.PROTECT,related_name="care_enrollments",null=True,blank=True)),
                ("status",models.CharField(max_length=12,choices=[("WAITLISTED","Waitlisted"),("ACTIVE","Active"),("CANCELLED","Cancelled"),("EXPIRED","Expired")],default="WAITLISTED")),
                ("readiness",models.CharField(max_length=12,choices=[("INCOMPLETE","Incomplete"),("BLOCKED","Blocked"),("READY","Ready")],default="INCOMPLETE")),
                ("start_date",models.DateField()),
                ("end_date",models.DateField(null=True,blank=True)),
                ("weekdays",models.JSONField(default=list)),
            ],
            options={"constraints":[models.UniqueConstraint(fields=["child","program","start_date"],name="dia_enroll_child_start_uq"),models.CheckConstraint(condition=models.Q(end_date__isnull=True)|models.Q(end_date__gte=models.F("start_date")),name="dia_enroll_dates_order_ck")],"indexes":[models.Index(fields=["school","site","status"],name="dia_enroll_school_site_idx"),models.Index(fields=["school","child"],name="dia_enroll_school_child_idx")]},
        ),
    ]
