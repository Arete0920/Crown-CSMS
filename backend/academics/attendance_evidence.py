"""Audit the existing canonical attendance store; do not duplicate attendance."""
from rest_framework.exceptions import ValidationError
from .operations_models import ClassroomAttendanceSession, ClassroomAttendanceAudit
from django.utils import timezone
from core.models import StudentIdentityLink
from .models import Enrollment


def expected_roster(section, day):
    # Today's authorized roster is known. Do not invent historical expectations.
    if day != timezone.localdate():
        return None
    students = list(Enrollment.objects.filter(school_id=section.school_id, section=section,
        student__school_id=section.school_id, student__is_active=True).values_list('student_id', flat=True))
    links = StudentIdentityLink.objects.filter(school_id=section.school_id, verification_status='verified',
        compatibility_student_id__in=students, compatibility_student__school_id=section.school_id,
        core_student__school_id=section.school_id).exclude(evidence_reference='')
    identities = {row.compatibility_student_id: str(row.core_student_id) for row in links if row.evidence_reference.strip()}
    return [{'student_id': str(student), 'core_student_id': identities.get(student)} for student in students]


def record_attendance_evidence(section, day, actor, changes, reason=''):
    session, _ = ClassroomAttendanceSession.objects.get_or_create(school_id=section.school_id, section=section, date=day,
        defaults={'expected_roster': expected_roster(section, day)})
    session.version += 1; session.save()
    ClassroomAttendanceAudit.objects.create(session=session, actor=actor, version=session.version, changes=changes, reason=reason)
    return session.version
