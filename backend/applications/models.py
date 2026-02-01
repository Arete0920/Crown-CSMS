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
