"""Staff review of explanations through existing canonical attendance evidence."""
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.exceptions import APIException, ValidationError
from .attendance_evidence import record_attendance_evidence
from .collaboration_models import ClassroomEvent, ClassroomRecord
from .models import Enrollment
from .submission_workflow_views import _uuid
from crown_api.models import AttendanceRecord


class ReviewConflict(APIException):
    status_code = 409
    default_detail = 'Attendance or explanation changed; refresh before reviewing.'


def pending_explanations(school, section, day):
    return ClassroomRecord.objects.filter(
        school_id=school, section=section, kind='absence_explanation',
        student__school_id=school, student__is_active=True,
        student_id__in=Enrollment.objects.filter(school_id=school, section=section).values('student_id'),
    ).exclude(state='resolved').filter(
        # Historical explanations can be undated. A reviewer must explicitly
        # confirm the selected roster date; no date is inferred from the title.
        Q(metadata__absence_date=day.isoformat()) | Q(metadata__absence_date__isnull=True)
    )


def review_explanation(*, school, section, day, actor, data, key, fingerprint):
    from .operations_models import ClassroomAttendanceSession
    from crown_api.views_academics import _verified_attendance_identity
    record = get_object_or_404(ClassroomRecord.objects.select_for_update(),
        school_id=school, section=section, kind='absence_explanation',
        id=_uuid(data.get('explanation_id'), 'explanation_id'),
        student__school_id=school, student__is_active=True)
    version = data.get('explanation_version')
    session = ClassroomAttendanceSession.objects.filter(school_id=school, section=section, date=day).first()
    attendance_version = data.get('version')
    if (isinstance(version, bool) or not isinstance(version, int) or version != record.version
            or record.state == 'resolved' or isinstance(attendance_version, bool)
            or not isinstance(attendance_version, int)
            or attendance_version != (session.version if session else 0)):
        raise ReviewConflict()
    if record.metadata.get('absence_date') not in (None, day.isoformat()):
        raise ValidationError('The explanation date must match the selected roster date.')
    if record.metadata.get('absence_date') is None and data.get('confirm_undated_date') is not True:
        raise ValidationError('Confirm the selected roster date for an undated explanation.')
    decision = data.get('decision')
    if decision not in {'excuse', 'decline'}:
        raise ValidationError('Choose excuse or decline.')
    note = data.get('reason')
    if not isinstance(note, str) or not note.strip() or len(note) > 20000:
        raise ValidationError('A review reason shared with the family is required (up to 20000 characters).')
    core, student = _verified_attendance_identity(record.student_id, school)
    get_object_or_404(Enrollment, school_id=school, section=section, student=student, student__is_active=True)
    attendance = get_object_or_404(AttendanceRecord.objects.select_for_update(), student=core, section=section, date=day)
    if attendance.status not in {'ABSENT', 'EXCUSED'}:
        raise ReviewConflict('Review requires an existing absent or excused attendance record.')
    before = attendance.status
    if decision == 'excuse':
        attendance.status = 'EXCUSED'
        attendance.save(update_fields=['status'])
    changes = [{'student_id': str(student.id), 'core_student_id': str(core.id),
                'before': before, 'after': attendance.status, 'explanation_id': str(record.id),
                'decision': decision}]
    version = record_attendance_evidence(section, day, actor, changes, note.strip())
    record.state = 'resolved'; record.version += 1
    record.save(update_fields=['state', 'version', 'updated_at'])
    ClassroomEvent.objects.create(record=record, student=student, actor=actor, request_key=key,
        fingerprint=fingerprint, action='attendance_review', payload={
            'date': day.isoformat(), 'decision': decision, 'note': note.strip(),
            'before': before, 'after': attendance.status, 'attendance_version': version})
    return {'saved': True, 'version': version, 'explanation_id': str(record.id),
            'explanation_version': record.version, 'decision': decision}
