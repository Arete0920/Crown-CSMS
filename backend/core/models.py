import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


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
        return f"{self.email} ({self.school.name})"


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
    ACCOUNT_CODE_CHOICES = [
        ('TUITION', 'Tuition'),
        ('AID', 'Aid'),
        ('FEE', 'Fee'),
        ('PAYMENT', 'Payment'),
    ]
    
    SOURCE_CHOICES = [
        ('TUITION_SET', 'Tuition Set'),
        ('AID_AWARD', 'Aid Award'),
        ('PAYMENT', 'Payment'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='ledger_entries')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='ledger_entries')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, blank=True, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    entry_date = models.DateField()
    account_code = models.CharField(max_length=20, choices=ACCOUNT_CODE_CHOICES)
    amount_cents = models.IntegerField()
    memo = models.TextField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    created_by_user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        ordering = ['-entry_date']
    
    def __str__(self):
        return f"{self.family.family_name} - {self.account_code} - {self.entry_date}"


# 14. AidApplication
class AidApplication(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('NEEDS_INFO', 'Needs Info'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='aid_applications')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='aid_applications')
    submitted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    household_size = models.IntegerField(blank=True, null=True)
    income_annual_cents = models.IntegerField(blank=True, null=True)
    notes_internal = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('school', 'family', 'academic_year')
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.family.family_name} - {self.academic_year.name} - {self.status}"


# 15. AidDocument
class AidDocument(BaseModel):
    DOC_TYPE_CHOICES = [
        ('W2', 'W2'),
        ('TAX_RETURN', 'Tax Return'),
        ('PAY_STUB', 'Pay Stub'),
        ('OTHER', 'Other'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='aid_documents')
    aid_application = models.ForeignKey(AidApplication, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES)
    received = models.BooleanField(default=False)
    received_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.aid_application.family.family_name} - {self.doc_type}"


# 16. AidReview
class AidReview(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='aid_reviews')
    aid_application = models.ForeignKey(AidApplication, on_delete=models.CASCADE, related_name='reviews')
    reviewer_user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    recommendation_cents = models.IntegerField(blank=True, null=True)
    recommendation_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Review: {self.aid_application.family.family_name} by {self.reviewer_user.email}"


# 17. AidAward
class AidAward(BaseModel):
    AWARD_TYPE_CHOICES = [
        ('NEED', 'Need'),
        ('MISSION', 'Mission'),
        ('MERIT', 'Merit'),
        ('HARDSHIP', 'Hardship'),
    ]
    
    DECISION_STATUS_CHOICES = [
        ('OFFERED', 'Offered'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='aid_awards')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='aid_awards')
    awarded_cents = models.IntegerField()
    award_type = models.CharField(max_length=50, choices=AWARD_TYPE_CHOICES)
    decision_status = models.CharField(max_length=50, choices=DECISION_STATUS_CHOICES, default='OFFERED')
    decided_by_user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, blank=True, null=True)
    decided_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('school', 'student', 'academic_year')
    
    def __str__(self):
        return f"{self.student.student_number} - {self.award_type} - {self.decision_status}"


# 18. AidAuditEvent
class AidAuditEvent(BaseModel):
    ENTITY_TYPE_CHOICES = [
        ('APPLICATION', 'Application'),
        ('REVIEW', 'Review'),
        ('AWARD', 'Award'),
    ]
    
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('SUBMITTED', 'Submitted'),
        ('SET_UNDER_REVIEW', 'Set Under Review'),
        ('NEEDS_INFO', 'Needs Info'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('AWARD_OFFERED', 'Award Offered'),
        ('AWARD_ACCEPTED', 'Award Accepted'),
        ('AWARD_DECLINED', 'Award Declined'),
        ('LETTER_READY', 'Letter Ready'),
        ('LETTER_SENT', 'Letter Sent'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='aid_audit_events')
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    actor_user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details_json = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.entity_type} - {self.action} - {self.timestamp}"
