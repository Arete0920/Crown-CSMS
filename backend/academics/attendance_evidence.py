"""Audit the existing canonical attendance store; do not duplicate attendance."""
from rest_framework.exceptions import ValidationError
from .operations_models import ClassroomAttendanceSession, ClassroomAttendanceAudit


def record_attendance_evidence(section, day, actor, changes, reason=''):
    session, _ = ClassroomAttendanceSession.objects.get_or_create(school_id=section.school_id, section=section, date=day)
    session.version += 1; session.save()
    ClassroomAttendanceAudit.objects.create(session=session, actor=actor, version=session.version, changes=changes, reason=reason)
    return session.version
