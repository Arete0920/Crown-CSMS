"""Fail-closed, canonical SIS evidence for bulk enrollment.

All reads and locks occur within the caller's atomic transaction. Lock order:
wizard session -> canonical applications -> family/applicant/identity links ->
legacy admissions rows -> core school-year enrollments. No identity or
enrollment is created from legacy names, inferred birth dates or statuses.
"""
from dataclasses import dataclass
from uuid import UUID

from admissions.models import AdmissionsApplication
from admissions.views_enroll import _CANONICAL_APPLICATION_RE
from applications.models import Application, Applicant
from applications.views_admissions import (
    CONTRACT_COUNTERSIGNED,
    DEPOSIT_PAID,
    DEPOSIT_WAIVED,
    _application_is_post_acceptance,
    _latest_enrollment_state_for_application,
)
from core.models import Enrollment, GradeLevel, HouseholdFamilyLink, StudentIdentityLink
from households.models import Student as CompatibilityStudent


class BulkEnrollmentProofError(ValueError):
    """One bad cohort member denies the complete transaction."""


@dataclass(frozen=True)
class VerifiedMember:
    legacy: AdmissionsApplication
    canonical: Application
    enrollment: Enrollment


def _canonical_reference(legacy):
    references = _CANONICAL_APPLICATION_RE.findall(str(legacy.notes_internal or ""))
    if len(references) != 1:
        raise BulkEnrollmentProofError("Exactly one canonical application reference is required.")
    try:
        return UUID(references[0])
    except (ValueError, TypeError) as exc:
        raise BulkEnrollmentProofError("Invalid canonical application reference.") from exc


def _identity_for_application(app, school_id):
    if app.school_id != school_id or app.household.school_id != school_id:
        raise BulkEnrollmentProofError("Canonical application and household must match the school.")
    state = _latest_enrollment_state_for_application(app)
    if (
        not _application_is_post_acceptance(app)
        or state.get("contract_status") != CONTRACT_COUNTERSIGNED
        or state.get("deposit_status") not in (DEPOSIT_PAID, DEPOSIT_WAIVED)
    ):
        raise BulkEnrollmentProofError("Accepted decision, countersigned contract and paid/waived deposit required.")
    links = list(
        HouseholdFamilyLink.objects.select_for_update(of=("self",))
        .filter(school_id=school_id, household_id=app.household_id)
        .order_by("pk")[:2]
    )
    if len(links) != 1 or links[0].family.school_id != school_id:
        raise BulkEnrollmentProofError("Exactly one same-school household-family association is required.")
    family_id = links[0].family_id
    applicants = list(
        Applicant.objects.select_for_update(of=("self",))
        .filter(application=app, school_id=school_id)
        .order_by("created_at", "pk")
    )
    if not applicants:
        raise BulkEnrollmentProofError("Canonical enrollment requires at least one applicant.")
    verified = {}
    for applicant in applicants:
        if applicant.dob is None or applicant.student_id is None:
            raise BulkEnrollmentProofError("Applicant must have an actual DOB and linked student identity.")
        compatibility = CompatibilityStudent.objects.filter(
            pk=applicant.student_id,
            school_id=school_id,
            household_id=app.household_id,
        ).first()
        if compatibility is None:
            raise BulkEnrollmentProofError("Applicant compatibility student belongs to another household or school.")
        link = (
            StudentIdentityLink.objects.select_for_update(of=("self",))
            .select_related("core_student")
            .filter(
                school_id=school_id,
                compatibility_student_id=applicant.student_id,
                source=StudentIdentityLink.SOURCE_ADMISSIONS,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference=f"application:{app.id}:applicant:{applicant.id}",
            )
            .first()
        )
        if link is None:
            raise BulkEnrollmentProofError("Exact verified applicant-bound canonical identity is required.")
        core = link.core_student
        if (
            core.school_id != school_id
            or core.family_id != family_id
            or core.dob != applicant.dob
            or core.status not in ("APPLICANT", "ACTIVE")
            or not str(core.student_number or "").strip()
            or str(core.student_number).upper().startswith("APP-")
            or str(core.first_name or "").strip().casefold()
               != str(applicant.first_name or "").strip().casefold()
            or str(core.last_name or "").strip().casefold()
               != str(applicant.last_name or "").strip().casefold()
        ):
            raise BulkEnrollmentProofError("Canonical student differs by family, DOB, name, school, status or number.")
        grade = GradeLevel.objects.filter(
            school_id=school_id,
            code=str(applicant.grade_applying_for or "").strip().upper(),
        ).first()
        if grade is None:
            raise BulkEnrollmentProofError("Applicant requires an authoritative school grade.")
        if core.id in verified:
            raise BulkEnrollmentProofError("Multiple applicants cannot claim one canonical student.")
        verified[core.id] = grade.id
    return family_id, verified


def verified_cohort(session, school_id, *, enrolled_only=False):
    """Verify full student, family, year and status provenance under row locks."""
    raw = session.application_ids
    if not isinstance(raw, list) or not raw:
        raise BulkEnrollmentProofError("A nonempty fixed cohort is required.")
    try:
        identifiers = [UUID(str(item)) for item in raw]
    except (ValueError, TypeError, AttributeError) as exc:
        raise BulkEnrollmentProofError("Selected admissions application ID is invalid.") from exc
    if len(identifiers) != len(set(identifiers)):
        raise BulkEnrollmentProofError("Duplicate selected application ID is not permitted.")
    # Discovery reads are untrusted; re-read and recheck after row locks.
    snapshots = list(
        AdmissionsApplication.objects.filter(
            pk__in=identifiers, school_id=school_id,
            academic_year__school_id=school_id,
            academic_year__name=session.academic_year_label,
            family__school_id=school_id,
        ).order_by("pk")
    )
    if len(snapshots) != len(identifiers):
        raise BulkEnrollmentProofError("Selected cohort changed school, year, or membership.")
    references = {row.pk: _canonical_reference(row) for row in snapshots}
    canonical_ids = set(references.values())
    canonical_rows = list(
        Application.objects.select_for_update(of=("self",))
        .select_related("household")
        .filter(pk__in=canonical_ids, school_id=school_id)
        .order_by("pk")
    )
    if len(canonical_rows) != len(canonical_ids):
        raise BulkEnrollmentProofError("Linked canonical application is missing.")
    canonical_by_id = {row.pk: row for row in canonical_rows}
    identity_by_id = {
        row.pk: _identity_for_application(row, school_id)
        for row in canonical_rows
    }
    legacy_rows = list(
        AdmissionsApplication.objects.select_for_update(of=("self",))
        .select_related("academic_year", "family")
        .filter(pk__in=identifiers, school_id=school_id)
        .order_by("pk")
    )
    if len(legacy_rows) != len(identifiers):
        raise BulkEnrollmentProofError("Selected legacy cohort changed.")
    used = set()
    members = []
    for legacy in legacy_rows:
        canonical_id = _canonical_reference(legacy)
        if canonical_id != references.get(legacy.pk):
            raise BulkEnrollmentProofError("Canonical provenance changed before legacy lock.")
        if (
            legacy.academic_year.school_id != school_id
            or legacy.academic_year.name != session.academic_year_label
            or legacy.family.school_id != school_id
            or legacy.status not in (
                AdmissionsApplication.STATUS_ACCEPTED,
                AdmissionsApplication.STATUS_ENROLLED,
            )
            or (enrolled_only and legacy.status != AdmissionsApplication.STATUS_ENROLLED)
        ):
            raise BulkEnrollmentProofError("Selected admissions row is not eligible for the requested school and year.")
        family_id, verified = identity_by_id[canonical_id]
        if legacy.family_id != family_id or legacy.student_id not in verified:
            raise BulkEnrollmentProofError("Legacy student or family is not a verified canonical applicant.")
        key = (canonical_id, legacy.student_id)
        if key in used:
            raise BulkEnrollmentProofError("Duplicate student in enrollment cohort.")
        used.add(key)
        record = (
            Enrollment.objects.select_for_update(of=("self",))
            .filter(
                school_id=school_id,
                student_id=legacy.student_id,
                academic_year_id=legacy.academic_year_id,
                grade_level_id=verified[legacy.student_id],
                grade_level__school_id=school_id,
                status="ENROLLED",
            )
            .first()
        )
        if record is None:
            raise BulkEnrollmentProofError("Persisted verified SIS enrollment is required before conversion.")
        members.append(VerifiedMember(legacy, canonical_by_id[canonical_id], record))
    for canonical_id, (_, expected) in identity_by_id.items():
        actual = {student_id for app_id, student_id in used if app_id == canonical_id}
        if actual != set(expected):
            raise BulkEnrollmentProofError("All canonical applicants must be included in one cohort.")
    return members
