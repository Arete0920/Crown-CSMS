import uuid
from django.db import models
from households.models import Household, Student


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class ApplicationStatus(models.TextChoices):
	DRAFT = "DRAFT", "Draft"
	SUBMITTED = "SUBMITTED", "Submitted"
	IN_REVIEW = "IN_REVIEW", "In Review"
	DECIDED = "DECIDED", "Decided"


class Application(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# multi-tenant anchor
	school_id = models.UUIDField(db_index=True)

	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="applications")

	status = models.CharField(
		max_length=20,
		choices=ApplicationStatus.choices,
		default=ApplicationStatus.DRAFT,
		db_index=True,
	)
	checklist_access_key = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)

	submitted_at = models.DateTimeField(null=True, blank=True)
	decided_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = "application"
		indexes = [
			models.Index(fields=["school_id", "status"]),
			models.Index(fields=["school_id", "created_at"]),
		]

	def __str__(self) -> str:
		return f"Application {self.id} ({self.status})"


class Applicant(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="applicants")

	# optional link to an existing student (usually null for brand-new applicants)
	student = models.ForeignKey(
		Student, null=True, blank=True, on_delete=models.SET_NULL, related_name="applicant_links"
	)

	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)

	grade_applying_for = models.CharField(max_length=16, blank=True, default="")
	dob = models.DateField(null=True, blank=True)

	# Admissions funnel fields (canonical)
	source = models.CharField(max_length=32, default="other", db_index=True)
	flags = models.JSONField(default=dict, blank=True)

	class Meta:
		db_table = "applicant"
		indexes = [
			models.Index(fields=["school_id", "application"]),
			models.Index(fields=["school_id", "last_name", "first_name"]),
		]

	def __str__(self) -> str:
		return f"{self.last_name}, {self.first_name}"


class ApplicationEvent(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="events")

	event_type = models.CharField(max_length=60)
	payload = models.JSONField(default=dict, blank=True)

	class Meta:
		db_table = "application_event"
		indexes = [
			models.Index(fields=["school_id", "application", "created_at"]),
			models.Index(fields=["school_id", "event_type"]),
		]

	def __str__(self) -> str:
		return f"{self.event_type}"


class ChecklistItemStatus(models.TextChoices):
	MISSING = "missing", "Missing"
	SUBMITTED = "submitted", "Submitted"
	UNDER_REVIEW = "under_review", "Under Review"
	APPROVED = "approved", "Approved"
	REJECTED = "rejected", "Rejected"


class EnrollmentContractStatus(models.TextChoices):
	DRAFT = "draft", "Draft"
	ISSUED = "issued", "Issued"
	SIGNED = "signed", "Signed"
	COUNTERSIGNED = "countersigned", "Countersigned"
	SUPERSEDED = "superseded", "Superseded"


class ApplicationChecklistItem(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="checklist_items")

	item_key = models.CharField(max_length=64)
	title = models.CharField(max_length=120)
	office = models.CharField(max_length=120, blank=True, default="")
	is_required = models.BooleanField(default=True)
	status = models.CharField(
		max_length=32,
		choices=ChecklistItemStatus.choices,
		default=ChecklistItemStatus.MISSING,
		db_index=True,
	)
	notes = models.TextField(blank=True, default="")
	submitted_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = "application_checklist_item"
		constraints = [
			models.UniqueConstraint(fields=["application", "item_key"], name="uniq_app_checklist_item_key"),
		]
		indexes = [
			models.Index(fields=["school_id", "application", "status"]),
		]

	def __str__(self) -> str:
		return f"{self.item_key} ({self.status})"


class ApplicationChecklistDocument(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	checklist_item = models.ForeignKey(ApplicationChecklistItem, on_delete=models.CASCADE, related_name="documents")

	file = models.FileField(upload_to="admissions/checklist/%Y/%m/%d")
	original_filename = models.CharField(max_length=255, blank=True, default="")
	content_type = models.CharField(max_length=120, blank=True, default="")
	uploaded_by = models.CharField(max_length=255, blank=True, default="")

	class Meta:
		db_table = "application_checklist_document"
		indexes = [
			models.Index(fields=["school_id", "checklist_item", "created_at"]),
		]

	def __str__(self) -> str:
		return self.original_filename or str(self.id)


class EnrollmentContract(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="enrollment_contracts")

	version = models.PositiveIntegerField(default=1)
	status = models.CharField(
		max_length=32,
		choices=EnrollmentContractStatus.choices,
		default=EnrollmentContractStatus.DRAFT,
		db_index=True,
	)
	line_items = models.JSONField(default=list, blank=True)
	contract_totals = models.JSONField(default=dict, blank=True)
	net_amount_cents = models.BigIntegerField(default=0)
	currency = models.CharField(max_length=3, default="USD")

	payment_plan = models.CharField(max_length=80, blank=True, default="")
	payment_schedule = models.CharField(max_length=255, blank=True, default="")
	responsible_payer = models.CharField(max_length=255, blank=True, default="")
	refund_terms = models.TextField(blank=True, default="")
	note = models.TextField(blank=True, default="")

	issued_at = models.DateTimeField(null=True, blank=True)
	signed_at = models.DateTimeField(null=True, blank=True)
	countersigned_at = models.DateTimeField(null=True, blank=True)
	amended_from = models.ForeignKey(
		"self",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="amendments",
	)
	created_by = models.CharField(max_length=255, blank=True, default="")

	class Meta:
		db_table = "enrollment_contract"
		constraints = [
			models.UniqueConstraint(fields=["application", "version"], name="uniq_enrollment_contract_version"),
		]
		indexes = [
			models.Index(fields=["school_id", "application", "status"]),
		]

	def __str__(self) -> str:
		return f"Contract v{self.version} ({self.status})"
