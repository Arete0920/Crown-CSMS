import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantSafeModel(models.Model):
    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise RuntimeError("Hard delete blocked for tenant-owned models. Use soft-delete or reversal.")

# 1. School
class School(BaseModel):
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default='America/New_York')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# 2. AcademicYear
class AcademicYear(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['start_date']

    def __str__(self):
        return f"{self.school.name} - {self.name}"


# 3. GradeLevel
class GradeLevel(BaseModel):
    GRADE_CHOICES = [
        ('PK', 'Pre-K'),
        ('K', 'Kindergarten'),
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
        ('10', 'Grade 10'),
        ('11', 'Grade 11'),
        ('12', 'Grade 12'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='grade_levels')
    code = models.CharField(max_length=3, choices=GRADE_CHOICES)
    label = models.CharField(max_length=50)
    sort_order = models.IntegerField()

    class Meta:
        unique_together = ('school', 'code')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.school.name} - {self.label}"


# 4. Family
class Family(BaseModel):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='families')
    family_name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    class Meta:
        unique_together = ('school', 'family_name')
        ordering = ['family_name']

    def __str__(self):
        return f"{self.family_name} ({self.school.name})"


# 5. Guardian
class Guardian(BaseModel):
    RELATIONSHIP_CHOICES = [
        ('MOTHER', 'Mother'),
        ('FATHER', 'Father'),
        ('GRANDPARENT', 'Grandparent'),
        ('GUARDIAN', 'Guardian'),
        ('OTHER', 'Other'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='guardians')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='guardians')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    portal_access = models.BooleanField(default=False)
    custody_flag = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'email')
        ordering = ['family', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.family.family_name})"


# 6. Student
class Student(BaseModel):
    STATUS_CHOICES = [
        ('APPLICANT', 'Applicant'),
        ('ACTIVE', 'Active'),
        ('WITHDRAWN', 'Withdrawn'),
        ('ALUMNI', 'Alumni'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='students')
    student_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLICANT')
    current_grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'student_number')
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_number})"


# 7. Staff
class Staff(BaseModel):
    ROLE_CHOICES = [
        ('TEACHER', 'Teacher'),
        ('DIRECTOR', 'Director'),
        ('ADMIN', 'Admin'),
        ('SUPPORT', 'Support'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='staff_members')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    class Meta:
        unique_together = ('school', 'email')
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role_type})"


# 8. UserAccount
class UserAccount(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='user_accounts', null=True, blank=True)
    staff = models.OneToOneField(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    guardian = models.OneToOneField(Guardian, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'email')

    def __str__(self):
        school_name = self.school.name if self.school else "No School"
        return f"{self.email} ({school_name})"


# 9. UserRole
class UserRole(BaseModel):
    ROLE_CODE_CHOICES = [
        ('HEAD_OF_SCHOOL', 'Head of School'),
        ('AID_DIRECTOR', 'Aid Director'),
        ('FINANCE_DIRECTOR', 'Finance Director'),
        ('REGISTRAR', 'Registrar'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
        ('STUDENT', 'Student'),
        ('SUPPORT', 'Support'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='user_roles')
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='roles')
    role_code = models.CharField(max_length=50, choices=ROLE_CODE_CHOICES)

    class Meta:
        unique_together = ('school', 'user', 'role_code')

    def __str__(self):
        return f"{self.user.email} - {self.role_code}"


# 10. Enrollment
class Enrollment(BaseModel):
    STATUS_CHOICES = [
        ('ENROLLED', 'Enrolled'),
        ('WITHDRAWN', 'Withdrawn'),
        ('GRADUATED', 'Graduated'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='enrollments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ENROLLED')

    class Meta:
        unique_together = ('school', 'student', 'academic_year')
        ordering = ['student__last_name', 'academic_year']

    def __str__(self):
        return f"{self.student.student_number} - {self.academic_year.name}"


# 11. TuitionPlan
class TuitionPlan(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='tuition_plans')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='tuition_plans')
    name = models.CharField(max_length=255)
    annual_amount_cents = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'academic_year', 'name')

    def __str__(self):
        return f"{self.name} - {self.school.name}"


# 12. StudentTuition
class StudentTuition(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='student_tuitions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tuitions')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    tuition_plan = models.ForeignKey(TuitionPlan, on_delete=models.CASCADE)
    annual_amount_cents = models.IntegerField()
    discounts_cents = models.IntegerField(default=0)
    net_annual_cents = models.IntegerField()

    class Meta:
        unique_together = ('school', 'student', 'academic_year')

    def __str__(self):
        return f"{self.student.student_number} - {self.academic_year.name}"


# 13. LedgerEntry
class LedgerEntry(BaseModel):
    SOURCE_TUITION_SET = 'TUITION_SET'
    SOURCE_AID_AWARD = 'AID_AWARD'
    SOURCE_FEE = 'FEE'
    SOURCE_PAYMENT = 'PAYMENT'
    SOURCE_ADJUSTMENT = 'ADJUSTMENT'

    SOURCE_CHOICES = [
        (SOURCE_TUITION_SET, 'Tuition Set'),
        (SOURCE_AID_AWARD, 'Aid Award'),
        (SOURCE_FEE, 'Fee'),
        (SOURCE_PAYMENT, 'Payment'),
        (SOURCE_ADJUSTMENT, 'Adjustment'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='ledger_entries')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='ledger_entries')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, blank=True, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    # Now points to ChartAccount instead of hardcoded string choices
    account = models.ForeignKey('finance.ChartAccount', on_delete=models.PROTECT, related_name='ledger_entries')
    batch = models.ForeignKey('finance.JournalBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    entry_date = models.DateField()
    amount_cents = models.IntegerField()  # can be +/- depending on debit/credit
    memo = models.TextField(blank=True, default='')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    created_by_user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, blank=True, null=True)

    # Reversal mechanism for immutable audit trail
    is_reversal = models.BooleanField(default=False)
    reversal_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversals'
    )

    class Meta:
        ordering = ['-entry_date', '-created_at']

    def delete(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry records are immutable. Use create_reversal().")

    def __str__(self):
        account_code = self.account.code if self.account_id else 'NoAccount'
        return f"{self.family.family_name} - {account_code} - {self.entry_date}"

    @staticmethod
    def create_reversal(original_entry, created_by=None, memo_suffix=" (REVERSAL)"):
        """
        Convenience method to reverse an existing entry.
        Creates a new LedgerEntry with negated amount, linking back to the original.
        """
        from django.utils import timezone
        return LedgerEntry.objects.create(
            school=original_entry.school,
            family=original_entry.family,
            student=original_entry.student,
            academic_year=original_entry.academic_year,
            account=original_entry.account,
            batch=original_entry.batch,
            entry_date=timezone.now().date(),
            amount_cents=-original_entry.amount_cents,
            memo=original_entry.memo + memo_suffix,
            source=original_entry.source,
            created_by_user=created_by,
            is_reversal=True,
            reversal_of=original_entry,
        )


# ──────────────────────────────────────────────────────────────────────────────
# LAYER 1 — CROWN PERMISSION ENGINE
#
# CrownPermission  — authoritative list of capability codes
# RolePermission   — maps role_code strings (from UserRole) to permissions
#
# Named "Crown" prefix to avoid collision with Django's built-in Permission
# model from django.contrib.auth.
# ──────────────────────────────────────────────────────────────────────────────

class CrownPermission(BaseModel):
    """
    A discrete, named capability within the Crown platform.
    Codes follow the pattern  <module>.<action>  e.g. "finance.view".
    """
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class RolePermission(BaseModel):
    """
    Grants a capability to everyone who holds a given role_code.
    role_code values must match UserRole.ROLE_CODE_CHOICES; no FK enforced so
    that new roles can be seeded before the choices list is updated.
    """
    role_code = models.CharField(max_length=50, db_index=True)
    permission = models.ForeignKey(
        CrownPermission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        unique_together = ("role_code", "permission")
        ordering = ["role_code", "permission__code"]

    def __str__(self):
        return f"{self.role_code} → {self.permission.code}"


# Ensure SeedRun is registered under the core app
from .models_seed import SeedRun  # noqa: E402,F401

# Data retention policies — registered under core app
from .models_retention import DataRetentionPolicy, RetentionPurgeAudit  # noqa: E402,F401


class HouseholdFamilyLink(BaseModel):
    """
    First-class bridge between a household (by UUID) and a core.Family.

    Replaces the temporary AdmissionsApplication bridge used in parent scoping
    (see crown_api/scoping_students.py). Supports multiple source types so the
    link can be created from admissions, enrollment, SIS import, or manually.

    unique_together = ('household_id', 'family') ensures one link per pair.
    """
    SOURCE_ADMISSIONS = 'admissions'
    SOURCE_ENROLLMENT = 'enrollment'
    SOURCE_IMPORT = 'import'
    SOURCE_MANUAL = 'manual'
    SOURCE_CHOICES = [
        (SOURCE_ADMISSIONS, 'From AdmissionsApplication'),
        (SOURCE_ENROLLMENT, 'From enrollment event'),
        (SOURCE_IMPORT, 'From SIS import'),
        (SOURCE_MANUAL, 'Manual linking'),
    ]

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='household_family_links',
    )
    household_id = models.UUIDField(db_index=True)
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='household_family_links',
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    class Meta:
        unique_together = ('household_id', 'family')

    def __str__(self):
        return f"HouseholdFamilyLink({self.household_id} ↔ {self.family_id})"


class StudentIdentityLink(BaseModel):
    """Explicit, tenant-safe crosswalk from canonical core.Student to households.Student."""

    SOURCE_ADMISSIONS = 'admissions'
    SOURCE_IMPORT = 'import'
    SOURCE_MANUAL = 'manual'
    SOURCE_RECONCILIATION = 'reconciliation'
    SOURCE_CHOICES = [
        (SOURCE_ADMISSIONS, 'Verified admissions conversion'),
        (SOURCE_IMPORT, 'Verified SIS import'),
        (SOURCE_MANUAL, 'Manual verified mapping'),
        (SOURCE_RECONCILIATION, 'Deterministic reconciliation'),
    ]

    STATUS_VERIFIED = 'verified'
    STATUS_PENDING = 'pending'
    STATUS_CHOICES = [
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_PENDING, 'Pending evidence'),
    ]

    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='student_identity_links',
    )
    core_student = models.OneToOneField(
        Student,
        on_delete=models.PROTECT,
        related_name='identity_link',
    )
    compatibility_student = models.OneToOneField(
        'households.Student',
        on_delete=models.PROTECT,
        related_name='core_identity_link',
    )
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    verification_status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_VERIFIED,
    )
    evidence_reference = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['school_id', 'core_student_id']
        indexes = [models.Index(fields=['school', 'verification_status'])]

    def clean(self):
        super().clean()
        errors = {}
        if self.core_student_id and self.core_student.school_id != self.school_id:
            errors['core_student'] = 'Canonical student must belong to the same school.'
        if self.compatibility_student_id and self.compatibility_student.school_id != self.school_id:
            errors['compatibility_student'] = 'Compatibility student must belong to the same school.'
        if self.verification_status == self.STATUS_VERIFIED and not self.evidence_reference.strip():
            errors['evidence_reference'] = 'Verified mappings require an evidence reference.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not kwargs.get('raw', False):
            self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"StudentIdentityLink({self.core_student_id} ↔ {self.compatibility_student_id})"
