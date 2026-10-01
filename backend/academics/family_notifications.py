"""In-app notices only. The deployment scheduler owns periodic invocation."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone
from .family_models import ClassroomFamilyNotice, ClassroomNotificationPreference


def queue_notice(school, account, key, title, thread=None, now=None):
    now = now or timezone.now()
    preference = ClassroomNotificationPreference.objects.filter(school_id=school, account=account).first()
    if preference and not preference.in_app:
        return None
    available = now
    if preference and preference.quiet_start and preference.quiet_end:
        local = now.astimezone(ZoneInfo(preference.timezone))
        clock = local.time().replace(tzinfo=None)
        start, end = preference.quiet_start, preference.quiet_end
        quiet = start <= clock < end if start < end else clock >= start or clock < end
        if quiet:
            day = local.date() + timedelta(days=1) if start >= end and clock >= start else local.date()
            available = datetime.combine(day, end, tzinfo=ZoneInfo(preference.timezone))
    return ClassroomFamilyNotice.objects.get_or_create(school_id=school, account=account, source_key=key,
             defaults={'thread': thread, 'title': title, 'available_at': available})[0]


def prepare_digests(now=None):
    from .experience_access import related_students
    now = now or timezone.now()
    count = 0
    for preference in ClassroomNotificationPreference.objects.filter(in_app=True, account__is_active=True).select_related('account'):
        local = now.astimezone(ZoneInfo(preference.timezone))
        if local.weekday() != preference.digest_day or not related_students(preference.account, preference.school_id, audience='parent').exists():
            continue
        week = local.date() - timedelta(days=local.weekday())
        before = ClassroomFamilyNotice.objects.filter(school_id=preference.school_id, account=preference.account, source_key=f'digest:{week}').exists()
        queue_notice(preference.school_id, preference.account, f'digest:{week}', 'Your weekly classroom digest is available', now=now)
        count += not before
    return count


def prepare_conference_reminders(now=None):
    from .family_models import ClassroomFamilyThread
    from .experience_access import related_students, taught_sections
    now = now or timezone.now()
    count = 0
    threads = ClassroomFamilyThread.objects.filter(kind='conference', state='open', slot__state='booked',
                   slot__starts_at__gt=now, slot__starts_at__lte=now + timedelta(hours=24)).select_related('guardian__account', 'slot__teacher', 'student')
    for row in threads:
        recipients = [row.guardian.account, row.slot.teacher]
        for account in recipients:
            if not account or not account.is_active:
                continue
            allowed = related_students(account, row.school_id, audience='parent').filter(id=row.student_id).exists() if account.id == row.guardian.account_id else taught_sections(account, row.school_id).filter(id=row.section_id).exists()
            if not allowed:
                continue
            key = f'conference:{row.id}:reminder'
            before = ClassroomFamilyNotice.objects.filter(school_id=row.school_id, account=account, source_key=key).exists()
            notice = queue_notice(row.school_id, account, key, 'Your classroom conference is within 24 hours', thread=row, now=now)
            count += bool(notice) and not before
    return count
