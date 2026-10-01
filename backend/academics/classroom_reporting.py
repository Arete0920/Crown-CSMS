"""Source-defined coverage and audited-session denominators for leadership."""
from core.models import StudentIdentityLink
from crown_api.models import AttendanceRecord
from .models import Assignment, PublisherObjective
from .operations_models import ClassroomAttendanceSession, validate_expected_roster


def coverage_rows(school, sections, lessons, start, end):
    rows = []
    for section in sections:
        objectives = PublisherObjective.objects.filter(school_id=school, lesson__school_id=school,
            lesson__unit__school_id=school, lesson__unit__course_id=section.course_id)
        expected = set(objectives.values_list('id', flat=True))
        links = lessons.filter(lesson_plan__section=section, lesson__school_id=school,
            lesson__unit__school_id=school, lesson__unit__course_id=section.course_id)
        planned = set(objectives.filter(lesson_id__in=links.values('lesson_id')).values_list('id', flat=True))
        taught = set(objectives.filter(lesson_id__in=links.filter(delivery_status='taught',
            actual_completed_at__isnull=False).values('lesson_id')).values_list('id', flat=True))
        assignments = Assignment.objects.filter(school_id=school, section=section, due_date__range=(start, end))
        aligned = assignments.filter(objective_id__in=expected, lesson_id__in=objectives.values('lesson_id'))
        # The assignment's lesson must match its objective, not just its course.
        from django.db.models import F
        aligned = aligned.filter(lesson_id=F('objective__lesson_id'))
        invalid = assignments.filter(objective__isnull=False).exclude(id__in=aligned.values('id')).count()
        rows.append({'section_id': section.id, 'known_objectives': len(expected), 'planned_objectives': len(planned),
            'confirmed_taught_objectives': len(taught), 'unplanned_objectives': len(expected - planned),
            'assessed_objectives': aligned.values('objective_id').distinct().count(), 'alignment_issues': invalid,
            'known_objective_delivery_percent': round(len(taught) * 100 / len(expected), 2) if expected else None})
    return rows


def attendance_summary(school, sections, start, end):
    sessions = list(ClassroomAttendanceSession.objects.filter(school_id=school, section__in=sections, date__range=(start, end)))
    valid_links = {(str(row.compatibility_student_id), str(row.core_student_id)) for row in
        StudentIdentityLink.objects.filter(school_id=school, verification_status='verified',
            compatibility_student__school_id=school, core_student__school_id=school).exclude(evidence_reference='')
        if row.evidence_reference.strip()}
    statuses = {(row.section_id, row.date, str(row.student_id)): row.status for row in
        AttendanceRecord.objects.filter(student__school_id=school, section__in=sections, date__range=(start, end))}
    expected = recorded = present = absent = tardy = excused = unknown = missing = unknown_rosters = 0
    for session in sessions:
        from django.core.exceptions import ValidationError
        try:
            validate_expected_roster(session.expected_roster)
        except ValidationError:
            unknown_rosters += 1
            continue
        if not isinstance(session.expected_roster, list):
            unknown_rosters += 1
            continue
        expected += len(session.expected_roster)
        for student in session.expected_roster:
            if (student['student_id'], student['core_student_id']) not in valid_links:
                unknown += 1
                continue
            status = statuses.get((session.section_id, session.date, student['core_student_id']))
            if status not in dict(AttendanceRecord.STATUS_CHOICES):
                missing += 1
                continue
            recorded += 1
            present += status in {'PRESENT', 'TARDY'}
            absent += status == 'ABSENT'
            tardy += status == 'TARDY'
            excused += status == 'EXCUSED'
    complete = expected > 0 and not (unknown_rosters or unknown or missing)
    return {'audited_attendance_sessions': len(sessions), 'sessions_without_expected_roster': unknown_rosters,
        'known_expected_student_sessions': expected, 'recorded_expected_statuses': recorded,
        'unverified_expected_identities': unknown, 'unrecorded_expected_statuses': missing,
        'audited_absences': absent, 'audited_tardy': tardy, 'audited_excused': excused,
        'audited_session_presence_percent': round(present * 100 / expected, 2) if complete else None}


def instructional_time_summary(lessons):
    rows = list(lessons.values('planned_minutes', 'actual_minutes'))
    planned = sum(row['planned_minutes'] or 0 for row in rows)
    actual = sum(row['actual_minutes'] or 0 for row in rows)
    missing = sum(row['planned_minutes'] is None or row['actual_minutes'] is None for row in rows)
    return {'lesson_links_missing_time_evidence': missing,
        'recorded_instructional_time_percent': round(actual * 100 / planned, 2) if rows and planned > 0 and missing == 0 else None}
