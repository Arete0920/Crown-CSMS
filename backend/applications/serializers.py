from rest_framework import serializers
from .models import Application, Applicant, ApplicationEvent


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = [
            "id", "school_id", "application", "student",
            "first_name", "last_name", "grade_applying_for",
            "dob", "source", "flags", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationEvent
        fields = ["id", "school_id", "application", "event_type", "payload", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    applicants = ApplicantSerializer(many=True, read_only=True)
    events = ApplicationEventSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "school_id", "household", "status",
            "submitted_at", "decided_at", "created_at", "updated_at",
            "applicants", "events",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]




class AdmissionsPublicConfigResponseSerializer(serializers.Serializer):
    application_fee = serializers.DictField()
    assessment_interview = serializers.DictField()


class AdmissionsSubmitResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    trace_id = serializers.CharField()
    application_id = serializers.UUIDField(allow_null=True)
    applicant_id = serializers.UUIDField(allow_null=True)
    application_ids = serializers.ListField(child=serializers.UUIDField())
    applicant_ids = serializers.ListField(child=serializers.UUIDField())
    application_count = serializers.IntegerField()
    stage = serializers.CharField()
    message = serializers.CharField()
    status_center = serializers.DictField()
    workflow_engine = serializers.DictField()
    documents_lifecycle = serializers.ListField(child=serializers.DictField())
    assessment_interview = serializers.DictField()
    enrollment_continuity = serializers.DictField()
    post_admission_lifecycle = serializers.DictField()
    communications_dispatch = serializers.DictField()
    reviewer_summary = serializers.DictField()
    family_affordability_profile = serializers.DictField()
    application_fee = serializers.DictField()
    application_fee_status_card = serializers.DictField()
    admissions_to_finance_handoff = serializers.DictField()
    fee_config = serializers.DictField()
    checklist_hub = serializers.DictField()
    next_step_orchestration = serializers.DictField()
    enrollment_contract_automation = serializers.DictField()


class AdmissionsDrilldownFlagsSerializer(serializers.Serializer):
    duplicate_suspected = serializers.BooleanField()
    bot_suspected = serializers.BooleanField()


class AdmissionsDrilldownRowSerializer(serializers.Serializer):
    lead_id = serializers.UUIDField()
    application_id = serializers.UUIDField()
    student_id = serializers.UUIDField(allow_null=True)
    stage = serializers.CharField()
    source = serializers.CharField()
    grade_applying_for = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    flags = AdmissionsDrilldownFlagsSerializer()


class AdmissionsDrilldownResponseSerializer(serializers.Serializer):
    academic_year = serializers.CharField()
    stage = serializers.CharField(allow_null=True)
    source = serializers.CharField(allow_null=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    rows = AdmissionsDrilldownRowSerializer(many=True)
    results = AdmissionsDrilldownRowSerializer(many=True)


class AdmissionsEnrollmentStateResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    application_status = serializers.CharField()
    contract_status = serializers.CharField()
    deposit_status = serializers.CharField()
    aid_award_status = serializers.CharField()
    aid_contract_sync_status = serializers.CharField()
    aid_billing_sync_status = serializers.CharField()
    aid_award_count = serializers.IntegerField()
    applicant_to_student_status = serializers.CharField()
    classroom_readiness_status = serializers.CharField()
    parent_portal_activation_status = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True)
    transition_reason = serializers.CharField(required=False, allow_blank=True)
    owner_assignment = serializers.CharField(required=False, allow_blank=True)
    trace_id = serializers.CharField(required=False, allow_blank=True)


class EnrollmentContractResponseSerializer(serializers.Serializer):
    contract_id = serializers.UUIDField()
    application_id = serializers.UUIDField()
    version = serializers.IntegerField()
    status = serializers.CharField()
    line_items = serializers.ListField(child=serializers.DictField())
    totals = serializers.DictField()
    payment_plan = serializers.CharField(allow_blank=True)
    payment_schedule = serializers.CharField(allow_blank=True)
    responsible_payer = serializers.CharField(allow_blank=True)
    refund_terms = serializers.CharField(allow_blank=True)
    note = serializers.CharField(allow_blank=True)
    amended_from = serializers.UUIDField(allow_null=True)
    issued_at = serializers.DateTimeField(allow_null=True)
    signed_at = serializers.DateTimeField(allow_null=True)
    countersigned_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
    m365_handoff = serializers.DictField()


class AdmissionsContractDetailResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    contract = EnrollmentContractResponseSerializer(allow_null=True)
    history = EnrollmentContractResponseSerializer(many=True)


class AdmissionsContractUpdateResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    contract = EnrollmentContractResponseSerializer()
    billing_handoff = serializers.DictField()


class AdmissionsContractAmendResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    contract = EnrollmentContractResponseSerializer()


class AdmissionsEventReplayEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)
    payload = serializers.DictField()


class AdmissionsEventReplayResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    count = serializers.IntegerField()
    events = AdmissionsEventReplayEventSerializer(many=True)
