from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import HouseholdFamilyLink, Student as CoreStudent, StudentIdentityLink
from core.permissions import user_has_permission

from . import views_admissions as legacy_views
from .models import Application, Applicant


@dataclass(frozen=True)
class VerifiedAdmissionsIdentity:
    applicant: Applicant
    core_student: CoreStudent


@dataclass(frozen=True)
class VerifiedAdmissionsContext:
    application: Application
    family: Any
    identities: tuple[VerifiedAdmissionsIdentity, ...]


def _identity_conflict(
    detail: str,
    *,
    code: str,
    applicant_id: Any | None = None,
) -> Response:
    payload: dict[str, Any] = {"detail": detail, "code": code}
    if applicant_id is not None:
        payload["applicant_id"] = str(applicant_id)
    return Response(payload, status=409)


def _verified_admissions_context(
    *,
    school,
    application_id,
) -> tuple[VerifiedAdmissionsContext | None, Response | None]:
    app = (
        Application.objects.select_for_update()
        .select_related("household")
        .filter(school_id=school.pk, id=application_id)
        .first()
    )
    if app is None:
        return None, Response(
            {"detail": legacy_views.APPLICATION_NOT_FOUND_DETAIL},
            status=404,
        )

    family_links = list(
        HouseholdFamilyLink.objects.select_for_update()
        .select_related("family")
        .filter(school=school, household_id=app.household_id)[:2]
    )
    if len(family_links) != 1:
        return None, _identity_conflict(
            "Enrollment conversion requires exactly one verified household-to-family link.",
            code="household_family_link_required",
        )
    family = family_links[0].family

    applicants = list(
        app.applicants.select_for_update()
        .select_related("student")
        .order_by("created_at", "id")
    )
    if not applicants:
        return None, _identity_conflict(
            "Enrollment conversion requires at least one applicant identity.",
            code="applicant_identity_required",
        )

    verified: list[VerifiedAdmissionsIdentity] = []
    for applicant in applicants:
        if applicant.student_id is None:
            return None, _identity_conflict(
                "Applicant must be linked to a verified compatibility student before enrollment conversion.",
                code="student_identity_link_required",
                applicant_id=applicant.id,
            )
        if (
            applicant.student.school_id != school.pk
            or applicant.student.household_id != app.household_id
        ):
            return None, _identity_conflict(
                "Applicant compatibility student does not match the application tenant and household.",
                code="compatibility_student_scope_mismatch",
                applicant_id=applicant.id,
            )

        link = (
            StudentIdentityLink.objects.select_for_update()
            .select_related("core_student", "compatibility_student")
            .filter(
                school=school,
                compatibility_student_id=applicant.student_id,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
            )
            .first()
        )
        if link is None:
            return None, _identity_conflict(
                "Applicant requires a verified canonical student identity mapping before enrollment conversion.",
                code="student_identity_link_required",
                applicant_id=applicant.id,
            )
        if not str(link.evidence_reference or "").strip():
            return None, _identity_conflict(
                "Verified student identity mapping is missing evidence provenance.",
                code="student_identity_evidence_required",
                applicant_id=applicant.id,
            )

        core_student = link.core_student
        if core_student.school_id != school.pk or core_student.family_id != family.id:
            return None, _identity_conflict(
                "Canonical student identity does not match the verified tenant and family boundary.",
                code="canonical_student_scope_mismatch",
                applicant_id=applicant.id,
            )
        student_number = str(core_student.student_number or "").strip()
        if not student_number or student_number.upper().startswith("APP-"):
            return None, _identity_conflict(
                "Canonical student requires an authoritative student number before enrollment conversion.",
                code="authoritative_student_number_required",
                applicant_id=applicant.id,
            )
        if (
            applicant.dob is None
            or core_student.dob is None
            or applicant.dob != core_student.dob
        ):
            return None, _identity_conflict(
                "Applicant and canonical student DOB must be present and identical before enrollment conversion.",
                code="student_dob_verification_required",
                applicant_id=applicant.id,
            )
        if (
            str(applicant.first_name or "").strip().casefold()
            != str(core_student.first_name or "").strip().casefold()
            or str(applicant.last_name or "").strip().casefold()
            != str(core_student.last_name or "").strip().casefold()
        ):
            return None, _identity_conflict(
                "Applicant and canonical student names must be reconciled before enrollment conversion.",
                code="student_name_reconciliation_required",
                applicant_id=applicant.id,
            )
        verified.append(
            VerifiedAdmissionsIdentity(
                applicant=applicant,
                core_student=core_student,
            )
        )

    return (
        VerifiedAdmissionsContext(
            application=app,
            family=family,
            identities=tuple(verified),
        ),
        None,
    )


def _sync_verified_legacy_application(
    *,
    context: VerifiedAdmissionsContext,
    academic_year,
    identity: VerifiedAdmissionsIdentity,
    target_status: str,
) -> str:
    from admissions.models import AdmissionsApplication

    app = context.application
    legacy_app, _ = AdmissionsApplication.objects.get_or_create(
        school=academic_year.school,
        academic_year=academic_year,
        family=context.family,
        student=identity.core_student,
        defaults={
            "status": target_status,
            "submitted_at": app.submitted_at,
            "notes_internal": f"canonical_application_id={app.id}",
        },
    )
    update_fields: list[str] = []
    if legacy_app.status != target_status:
        legacy_app.status = target_status
        update_fields.append("status")
    if legacy_app.submitted_at is None and app.submitted_at is not None:
        legacy_app.submitted_at = app.submitted_at
        update_fields.append("submitted_at")
    canonical_note = f"canonical_application_id={app.id}"
    if canonical_note not in str(legacy_app.notes_internal or ""):
        legacy_app.notes_internal = (
            f"{legacy_app.notes_internal}\n{canonical_note}".strip()
        )
        update_fields.append("notes_internal")
    if update_fields:
        legacy_app.save(update_fields=update_fields + ["updated_at"])
    return str(legacy_app.id)


def _upsert_verified_legacy_admissions(
    *,
    school,
    context: VerifiedAdmissionsContext,
    actor_user,
    target_status: str,
) -> tuple[dict[str, Any] | None, Response | None]:
    try:
        from admissions.models import AdmissionsApplication
    except Exception:
        return None, Response(
            {"detail": "Admissions compatibility module is unavailable."},
            status=503,
        )

    academic_year = legacy_views._resolve_legacy_academic_year(school=school)
    if academic_year is None:
        return None, _identity_conflict(
            "Enrollment conversion requires an authoritative academic year.",
            code="academic_year_required",
        )

    synced_ids = [
        _sync_verified_legacy_application(
            context=context,
            academic_year=academic_year,
            identity=identity,
            target_status=target_status,
        )
        for identity in context.identities
    ]

    session_state = None
    if target_status == AdmissionsApplication.STATUS_ENROLLED and synced_ids:
        session_state = legacy_views._create_legacy_conversion_session(
            school=school,
            actor_user=actor_user,
            academic_year=academic_year,
            application_ids=synced_ids,
            target_status=target_status,
        )

    return {
        "state": target_status.lower(),
        "count": len(synced_ids),
        "application_ids": synced_ids,
        "conversion_session": session_state,
    }, None


def _authorize_admissions_write(request, application_id):
    school, tenant_error = legacy_views._resolve_school(request)
    if tenant_error is not None:
        return None, None, tenant_error
    if not user_has_permission(
        request.user,
        legacy_views.ADMISSIONS_EDIT_PERMISSION,
        school=school,
    ):
        return None, None, Response(
            {"detail": legacy_views.PERMISSION_DENIED_DETAIL},
            status=403,
        )
    app = (
        Application.objects.select_for_update()
        .select_related("household")
        .filter(school_id=school.pk, id=application_id)
        .first()
    )
    if app is None:
        return school, None, Response(
            {"detail": legacy_views.APPLICATION_NOT_FOUND_DETAIL},
            status=404,
        )
    return school, app, None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_enrollment_state_update(request, application_id):
    with transaction.atomic():
        school, app, error = _authorize_admissions_write(request, application_id)
        if error is not None:
            return error
        assert school is not None and app is not None

        current = legacy_views._latest_enrollment_state_for_application(app)
        requested_contract = (
            (request.data or {}).get("contract_status") or current["contract_status"]
        )
        requested_deposit = (
            (request.data or {}).get("deposit_status") or current["deposit_status"]
        )
        note = str((request.data or {}).get("note") or "").strip()[:500]
        transition_reason = str(
            (request.data or {}).get("transition_reason") or ""
        ).strip()[:280]
        owner_assignment = str(
            (request.data or {}).get("owner_assignment") or ""
        ).strip()[:180]
        trace_id = legacy_views._request_trace_id(request)
        validation_error = legacy_views._validate_enrollment_state_update_request(
            app=app,
            current=current,
            requested_contract=requested_contract,
            requested_deposit=requested_deposit,
        )
        if validation_error is not None:
            return validation_error

        context, identity_error = _verified_admissions_context(
            school=school,
            application_id=app.id,
        )
        if identity_error is not None:
            return identity_error
        assert context is not None

        try:
            contract_record, billing_handoff = legacy_views._commit_enrollment_state_update(
                school=school,
                app=app,
                request_payload=request.data if isinstance(request.data, dict) else {},
                actor_user=request.user,
                requested_contract=requested_contract,
                requested_deposit=requested_deposit,
                note=note,
                transition_reason=transition_reason,
                owner_assignment=owner_assignment,
                trace_id=trace_id,
            )
        except ValidationError as exc:
            transaction.set_rollback(True)
            return Response({"detail": "; ".join(exc.messages)}, status=409)
        legacy_bridge, bridge_error = _upsert_verified_legacy_admissions(
            school=school,
            context=context,
            actor_user=request.user,
            target_status="ACCEPTED",
        )
        if bridge_error is not None:
            transaction.set_rollback(True)
            return bridge_error

        state = legacy_views._latest_enrollment_state_for_application(app)
        return Response(
            {
                "application_id": str(app.id),
                "application_status": app.status,
                "contract_record": legacy_views._serialize_enrollment_contract(
                    contract_record
                ),
                "billing_handoff": billing_handoff,
                "legacy_conversion_bridge": legacy_bridge,
                "transition_reason": transition_reason,
                "owner_assignment": owner_assignment,
                "trace_id": trace_id,
                **state,
            },
            status=200,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_lifecycle_chain_update(request, application_id):
    with transaction.atomic():
        school, app, error = _authorize_admissions_write(request, application_id)
        if error is not None:
            return error
        assert school is not None and app is not None

        if not legacy_views._application_is_post_acceptance(app):
            return Response(
                {
                    "detail": "Lifecycle handoff can be updated only after acceptance.",
                    "application_status": app.status,
                },
                status=409,
            )

        payload = request.data if isinstance(request.data, dict) else {}
        note = str(payload.get("note") or "").strip()[:500]
        (
            requested_enrollment,
            requested_classroom_ready,
            requested_portal_activation,
        ) = legacy_views._lifecycle_chain_request_flags(payload)
        if any(
            [
                requested_enrollment,
                requested_classroom_ready,
                requested_portal_activation,
            ]
        ):
            state = legacy_views._latest_enrollment_state_for_application(app)
            validation_error = legacy_views._validate_lifecycle_chain_request(
                app=app,
                state=state,
                requested_enrollment=requested_enrollment,
                requested_classroom_ready=requested_classroom_ready,
                requested_portal_activation=requested_portal_activation,
            )
            if validation_error is not None:
                return validation_error

        context, identity_error = _verified_admissions_context(
            school=school,
            application_id=app.id,
        )
        if identity_error is not None:
            return identity_error
        assert context is not None

        created_events, update_error = legacy_views._apply_lifecycle_chain_updates(
            app=app,
            actor_user=request.user,
            note=note,
            request_payload=payload,
        )
        if update_error is not None:
            return update_error

        target_status = (
            "ENROLLED"
            if legacy_views.ENROLLMENT_CONFIRMED_EVENT_TYPE in (created_events or [])
            or legacy_views._application_has_event(
                app,
                legacy_views.ENROLLMENT_CONFIRMED_EVENT_TYPE,
            )
            else "ACCEPTED"
        )
        legacy_bridge, bridge_error = _upsert_verified_legacy_admissions(
            school=school,
            context=context,
            actor_user=request.user,
            target_status=target_status,
        )
        if bridge_error is not None:
            transaction.set_rollback(True)
            return bridge_error

        state = legacy_views._latest_enrollment_state_for_application(app)
        return Response(
            {
                "application_id": str(app.id),
                "application_status": app.status,
                "created_events": created_events or [],
                "legacy_conversion_bridge": legacy_bridge,
                **state,
            },
            status=200,
        )
