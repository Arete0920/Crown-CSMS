from __future__ import annotations

from django.db.models import Exists, F, OuterRef
from django.utils import timezone

from core.models import (
    AcademicYear,
    Enrollment,
    Family,
    Guardian,
    Student,
    StudentIdentityLink,
    UserAccount,
)
from households.models import Student as CompatibilityStudent


def _check(*, check_id: str, label: str, severity: str, count: int, description: str, action: str) -> dict:
    return {
        "id": check_id,
        "label": label,
        "severity": severity,
        "count": int(count),
        "status": "pass" if int(count) == 0 else "review",
        "description": description,
        "action": action,
    }


def build_school_data_quality_summary(*, school_id) -> dict:
    """
    Return an aggregate, read-only school data-quality snapshot.

    The payload intentionally contains no names, emails, record identifiers, or
    automatic remediation instructions. It is designed for tenant-authorized
    administrators to identify data conditions that require review.
    """

    active_students = Student.objects.filter(school_id=school_id, status="ACTIVE")
    current_year_count = AcademicYear.objects.filter(
        school_id=school_id,
        is_current=True,
    ).count()

    current_enrollment = Enrollment.objects.filter(
        school_id=school_id,
        student_id=OuterRef("pk"),
        academic_year__school_id=school_id,
        academic_year__is_current=True,
        status="ENROLLED",
    )
    active_students_without_current_enrollment = (
        active_students.annotate(has_current_enrollment=Exists(current_enrollment))
        .filter(has_current_enrollment=False)
        .count()
    )

    active_students_missing_grade = active_students.filter(
        current_grade_level__isnull=True
    ).count()

    active_students_without_identity_link = active_students.filter(
        identity_link__isnull=True
    ).count()

    pending_identity_links = StudentIdentityLink.objects.filter(
        school_id=school_id,
        verification_status=StudentIdentityLink.STATUS_PENDING,
    ).count()

    verified_links_without_evidence = StudentIdentityLink.objects.filter(
        school_id=school_id,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="",
    ).count()

    active_family_qs = Family.objects.filter(
        school_id=school_id,
        status="ACTIVE",
        students__status="ACTIVE",
    ).distinct()
    same_school_guardian = Guardian.objects.filter(
        school_id=school_id,
        family_id=OuterRef("pk"),
    )
    active_families_without_guardians = (
        active_family_qs.annotate(has_guardian=Exists(same_school_guardian))
        .filter(has_guardian=False)
        .count()
    )

    active_portal_account = UserAccount.objects.filter(
        school_id=school_id,
        guardian_id=OuterRef("pk"),
        is_active=True,
    )
    portal_guardians_without_active_account = (
        Guardian.objects.filter(
            school_id=school_id,
            portal_access=True,
        )
        .annotate(has_active_account=Exists(active_portal_account))
        .filter(has_active_account=False)
        .count()
    )

    compatibility_students_without_link = CompatibilityStudent.objects.filter(
        school_id=school_id,
        is_active=True,
        core_identity_link__isnull=True,
    ).count()

    cross_tenant_relationships = sum(
        [
            Student.objects.filter(school_id=school_id)
            .exclude(family__school_id=F("school_id"))
            .count(),
            Guardian.objects.filter(school_id=school_id)
            .exclude(family__school_id=F("school_id"))
            .count(),
            Enrollment.objects.filter(school_id=school_id)
            .exclude(student__school_id=F("school_id"))
            .count(),
            Enrollment.objects.filter(school_id=school_id)
            .exclude(academic_year__school_id=F("school_id"))
            .count(),
            Enrollment.objects.filter(school_id=school_id)
            .exclude(grade_level__school_id=F("school_id"))
            .count(),
            StudentIdentityLink.objects.filter(school_id=school_id)
            .exclude(core_student__school_id=F("school_id"))
            .count(),
            StudentIdentityLink.objects.filter(school_id=school_id)
            .exclude(compatibility_student__school_id=F("school_id"))
            .count(),
        ]
    )

    current_year_issue_count = 0 if current_year_count == 1 else max(1, current_year_count - 1)

    checks = [
        _check(
            check_id="cross_tenant_relationship_integrity",
            label="Cross-tenant relationship integrity",
            severity="critical",
            count=cross_tenant_relationships,
            description="Counts school-owned relationships whose referenced record belongs to another school.",
            action="Review and correct the relationship through the owning workflow; do not bulk-reassign identities.",
        ),
        _check(
            check_id="current_academic_year_configuration",
            label="Current academic year configuration",
            severity="high",
            count=current_year_issue_count,
            description=f"Exactly one current academic year is expected; found {current_year_count}.",
            action="Review academic-year configuration before enrollment, attendance, or grading activity continues.",
        ),
        _check(
            check_id="active_student_current_enrollment",
            label="Active students without current-year enrollment",
            severity="high",
            count=active_students_without_current_enrollment,
            description="Active canonical students should have an enrolled record in the current academic year.",
            action="Review enrollment lifecycle state and current-year placement.",
        ),
        _check(
            check_id="active_student_grade_assignment",
            label="Active students without grade assignment",
            severity="medium",
            count=active_students_missing_grade,
            description="Active canonical students are missing a current grade-level assignment.",
            action="Review registrar placement before schedules, reporting, or promotion workflows rely on the record.",
        ),
        _check(
            check_id="canonical_student_identity_bridge",
            label="Active students without identity bridge",
            severity="medium",
            count=active_students_without_identity_link,
            description="Active canonical students are not linked to the compatibility student identity used by remaining legacy consumers.",
            action="Use approved identity reconciliation and verified mapping workflows; never infer mappings from names or email.",
        ),
        _check(
            check_id="pending_student_identity_evidence",
            label="Pending student identity mappings",
            severity="medium",
            count=pending_identity_links,
            description="Student identity mappings exist but still require verification evidence.",
            action="Complete the approved evidence review before treating the mapping as verified.",
        ),
        _check(
            check_id="verified_identity_missing_evidence",
            label="Verified identity mappings missing evidence",
            severity="high",
            count=verified_links_without_evidence,
            description="A verified student identity mapping lacks the required evidence reference.",
            action="Investigate provenance and correct the verification state or evidence reference.",
        ),
        _check(
            check_id="active_family_guardian_coverage",
            label="Active families without guardians",
            severity="medium",
            count=active_families_without_guardians,
            description="Active families with active students have no same-school canonical guardian record.",
            action="Review family and guardian setup before enabling family communications or portal workflows.",
        ),
        _check(
            check_id="portal_guardian_account_readiness",
            label="Portal-enabled guardians without active account",
            severity="medium",
            count=portal_guardians_without_active_account,
            description="Canonical guardians marked for portal access do not have an active same-school user account.",
            action="Review account linkage and access status; email similarity alone is not authorization.",
        ),
        _check(
            check_id="compatibility_student_bridge_coverage",
            label="Compatibility students without canonical bridge",
            severity="low",
            count=compatibility_students_without_link,
            description="Active compatibility student rows are not linked to canonical student identity.",
            action="Track these records through the governed convergence process before retiring compatibility readers.",
        ),
    ]

    severity_counts = {
        severity: sum(check["count"] for check in checks if check["severity"] == severity)
        for severity in ("critical", "high", "medium", "low")
    }
    findings_count = sum(check["count"] for check in checks)

    if severity_counts["critical"]:
        overall_status = "critical"
    elif severity_counts["high"]:
        overall_status = "action_required"
    elif severity_counts["medium"]:
        overall_status = "needs_review"
    elif severity_counts["low"]:
        overall_status = "monitor"
    else:
        overall_status = "healthy"

    return {
        "schema_version": 1,
        "mode": "read_only",
        "automatic_remediation": False,
        "school_id": str(school_id),
        "generated_at": timezone.now().isoformat(),
        "status": overall_status,
        "summary": {
            "findings_count": findings_count,
            **severity_counts,
        },
        "checks": checks,
    }
