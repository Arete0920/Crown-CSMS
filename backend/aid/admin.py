from django.contrib import admin
from .models import AidApplication, AidDocument, AidReview, AidAward, AidAuditEvent


@admin.register(AidApplication)
class AidApplicationAdmin(admin.ModelAdmin):
    list_display = ('school', 'academic_year', 'family', 'status', 'submitted_at')
    list_filter = ('school', 'academic_year', 'status', 'submitted_at')
    search_fields = ('family__family_name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AidDocument)
class AidDocumentAdmin(admin.ModelAdmin):
    list_display = ('school', 'aid_application', 'doc_type', 'received', 'received_at')
    list_filter = ('school', 'doc_type', 'received')
    search_fields = ('aid_application__family__family_name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AidReview)
class AidReviewAdmin(admin.ModelAdmin):
    list_display = ('school', 'aid_application', 'reviewer_user', 'started_at', 'completed_at', 'recommendation_cents')
    list_filter = ('school', 'started_at', 'completed_at')
    search_fields = ('aid_application__family__family_name', 'reviewer_user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AidAward)
class AidAwardAdmin(admin.ModelAdmin):
    list_display = ('school', 'student', 'academic_year', 'award_type', 'awarded_cents', 'decision_status', 'decided_at')
    list_filter = ('school', 'academic_year', 'award_type', 'decision_status')
    search_fields = ('student__student_number', 'student__last_name')
    readonly_fields = ('created_at', 'updated_at', 'ledger_entry')


@admin.register(AidAuditEvent)
class AidAuditEventAdmin(admin.ModelAdmin):
    list_display = ('school', 'entity_type', 'action', 'actor_user', 'timestamp')
    list_filter = ('school', 'entity_type', 'action', 'timestamp')
    search_fields = ('actor_user__email', 'action')
    readonly_fields = ('created_at', 'updated_at', 'timestamp', 'details_json')
