from __future__ import annotations

from collections import Counter


def build_internal_school_context(*, school_id, academic_year=None):
    from aid.models import AidAward
    from applications.models import Applicant
    from core.models import Enrollment
    from enrollment_period_wizard.models import GradeCapacity

    enrollment_qs = Enrollment.objects.filter(school_id=school_id, status="ENROLLED")
    capacity_qs = GradeCapacity.objects.filter(school_id=school_id)
    aid_qs = AidAward.objects.filter(school_id=school_id, decision_status=AidAward.DECISION_ACCEPTED)
    if academic_year is not None:
        enrollment_qs = enrollment_qs.filter(academic_year=academic_year)
        capacity_qs = capacity_qs.filter(academic_year=academic_year)
        aid_qs = aid_qs.filter(academic_year=academic_year)

    enrolled_by_grade = Counter(enrollment_qs.values_list("grade_level__code", flat=True))
    capacities = []
    for row in capacity_qs.values("grade_code", "target_seats", "new_students_allowed"):
        enrolled = int(enrolled_by_grade.get(row["grade_code"], 0))
        target = int(row["target_seats"] or 0)
        capacities.append({
            "grade_code": row["grade_code"],
            "target_seats": target,
            "enrolled": enrolled,
            "empty_seats": max(target - enrolled, 0),
            "new_students_allowed": bool(row["new_students_allowed"]),
        })

    aid_total = sum(aid_qs.values_list("awarded_cents", flat=True))
    sources = Counter(
        str(value or "Unspecified").strip() or "Unspecified"
        for value in Applicant.objects.filter(school_id=school_id).values_list("source", flat=True)
    )
    return {
        "current_enrollment": enrollment_qs.count(),
        "grade_capacity": capacities,
        "accepted_aid_cents": int(aid_total),
        "top_admissions_sources": [{"source": k, "count": v} for k, v in sources.most_common(10)],
    }


def build_market_study_snapshot(study):
    return {
        "study_id": str(study.id),
        "name": study.name,
        "status": study.status,
        "analysis_year": study.analysis_year,
        "layers": {
            "geography": study.geography or {},
            "population": study.population or {},
            "economics": study.economics or {},
            "education_market": study.education_market or {},
            "faith_community": study.faith_community or {},
            "competition": study.competition or {},
            "internal_context": study.internal_context or {},
        },
        "strategic_objectives": study.strategic_objectives or {},
        "source_provenance": study.source_provenance or [],
        "recommendations": [
            {
                "id": str(rec.id), "category": rec.category, "priority": rec.priority,
                "title": rec.title, "rationale": rec.rationale, "evidence": rec.evidence,
                "status": rec.status,
            }
            for rec in study.recommendations.all()[:50]
        ],
        "decision_domains": [
            "tuition", "affordability", "financial_aid", "enrollment",
            "programs", "marketing", "transportation", "expansion",
        ],
    }


def validate_market_inputs(data):
    required_sections = [
        "school_profile", "geography", "economics", "student_market", "competition",
        "faith_community", "enrollment_performance", "financial_profile", "program_capacity",
        "strategic_objectives",
    ]
    missing = [key for key in required_sections if not isinstance(data.get(key), dict)]
    return missing
