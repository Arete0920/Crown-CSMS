from django.contrib import admin, messages
from django.db.models import Count, Q, Sum

from .models import (
    AidApplication,
    AidDocument,
    AidReview,
    AidAward,
    AidAuditEvent,
    AidFinancialProfile,
    AidFinancialLineItem,
    AidHouseholdMember,
    AidQuestion,
    AidResponse,
)
from finance.models import JournalBatch, ChartAccount


@admin.action(description="Accept + Post selected awards to Ledger (AID)")
def accept_and_post_awards(modeladmin, request, queryset):
    posted = 0
    skipped = 0
    failed = 0

    batches = {}

    for award in queryset.select_related("school", "academic_year"):
        try:
            if award.ledger_entry_id:
                skipped += 1
                continue

            key = (award.school_id, award.academic_year_id)
            if key not in batches:
                batches[key] = JournalBatch.objects.create(
                    school=award.school,
                    academic_year=award.academic_year,
                    description="Aid Awards - Admin Post",
                    status="OPEN",
                    created_by=getattr(request.user, "useraccount", None) if hasattr(request.user, "useraccount") else None,
                )

            award.mark_accepted_and_post(
                actor_user=getattr(request.user, "useraccount", None),
                batch=batches[key],
            )
            posted += 1
        except ChartAccount.DoesNotExist:
            failed += 1
        except Exception:
            failed += 1

    if failed:
        modeladmin.message_user(
            request,
            f"Posted {posted}. Skipped {skipped}. Failed {failed}. (Check ChartAccount code='AID' exists for the school.)",
            level=messages.WARNING,
        )
    else:
        modeladmin.message_user(request, f"Posted {posted}. Skipped {skipped}.", level=messages.SUCCESS)


class ApplicationPriorityFilter(admin.SimpleListFilter):
    title = "Aid Director Queue"
    parameter_name = "queue"

    def lookups(self, request, model_admin):
        return [
            ("submitted", "Submitted (new)"),
            ("needs_info", "Needs Info"),
            ("under_review", "Under Review"),
            ("decided", "Decided (approved/denied)"),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "submitted":
            return queryset.filter(status=AidApplication.STATUS_SUBMITTED)
        if v == "needs_info":
            return queryset.filter(status=AidApplication.STATUS_NEEDS_INFO)
        if v == "under_review":
            return queryset.filter(status=AidApplication.STATUS_UNDER_REVIEW)
        if v == "decided":
            return queryset.filter(status__in=[AidApplication.STATUS_APPROVED, AidApplication.STATUS_DENIED])
        return queryset


@admin.register(AidApplication)
class AidApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "academic_year",
        "family",
        "status",
        "submitted_at",
        "household_size",
        "income_annual_cents",
    )
    list_filter = ("school", "academic_year", ApplicationPriorityFilter, "status")
    search_fields = ("family__family_name",)
    ordering = ("status", "-submitted_at", "-created_at")


@admin.register(AidDocument)
class AidDocumentAdmin(admin.ModelAdmin):
    list_display = ("school", "aid_application", "doc_type", "received", "received_at")
    list_filter = ("school", "doc_type", "received")
    search_fields = ("aid_application__family__family_name",)


@admin.register(AidReview)
class AidReviewAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "aid_application",
        "reviewer_user",
        "started_at",
        "completed_at",
        "recommendation_cents",
    )
    list_filter = ("school",)
    search_fields = ("aid_application__family__family_name", "reviewer_user__email")


class AwardWorkflowFilter(admin.SimpleListFilter):
    title = "Award Workflow"
    parameter_name = "workflow"

    def lookups(self, request, model_admin):
        return [
            ("offered", "Offered"),
            ("accepted_not_posted", "Accepted but NOT posted"),
            ("posted", "Posted to Ledger"),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "offered":
            return queryset.filter(decision_status=AidAward.DECISION_OFFERED)
        if v == "accepted_not_posted":
            return queryset.filter(decision_status=AidAward.DECISION_ACCEPTED, ledger_entry__isnull=True)
        if v == "posted":
            return queryset.filter(ledger_entry__isnull=False)
        return queryset


@admin.register(AidAward)
class AidAwardAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "student", "award_type", "awarded_cents", "decision_status", "decided_at", "ledger_entry")
    list_filter = ("school", "academic_year", "award_type", "decision_status", AwardWorkflowFilter)
    search_fields = ("student__last_name", "student__first_name", "student__student_number", "student__family__family_name")
    actions = [accept_and_post_awards]
    ordering = ("-created_at",)


@admin.register(AidAuditEvent)
class AidAuditEventAdmin(admin.ModelAdmin):
    list_display = ("school", "timestamp", "entity_type", "action", "actor_user")
    list_filter = ("school", "entity_type", "action")
    search_fields = ("action", "actor_user__email")
    ordering = ("-timestamp",)


class AidHouseholdMemberInline(admin.TabularInline):
    model = AidHouseholdMember
    extra = 0


class AidFinancialLineItemInline(admin.TabularInline):
    model = AidFinancialLineItem
    extra = 0
    readonly_fields = ("source_type", "source_reference", "verified_at", "verified_by")


@admin.register(AidFinancialProfile)
class AidFinancialProfileAdmin(admin.ModelAdmin):
    list_display = (
        "school", "academic_year", "family", "verification_status",
        "confirmed_at", "last_verified_at", "carried_forward_from",
    )
    list_filter = ("school", "academic_year", "verification_status", "consent_to_reuse")
    search_fields = ("family__family_name",)
    inlines = [AidHouseholdMemberInline, AidFinancialLineItemInline]


class AidResponseInline(admin.TabularInline):
    model = AidResponse
    extra = 0


@admin.register(AidQuestion)
class AidQuestionAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "key", "prompt", "response_type", "required", "active")
    list_filter = ("school", "academic_year", "response_type", "required", "active")
    search_fields = ("key", "prompt")
    ordering = ("school", "academic_year", "display_order", "id")
    inlines = [AidResponseInline]
