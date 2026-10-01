from datetime import datetime, timedelta, timezone as dt_timezone
import pytest
from django.conf import settings
from academics.tests.test_classroom_experience import classroom
from academics.family_models import ClassroomNotificationPreference, ClassroomFamilyNotice, ClassroomConferenceSlot, ClassroomFamilyThread
from academics.family_notifications import prepare_conference_reminders
from households.models import Guardian
from academics.tasks import prepare_classroom_notices

pytestmark=pytest.mark.django_db


def test_registered_task_uses_existing_scheduler_and_deduplicates_weekly_notices(classroom, monkeypatch):
    c=classroom;now=datetime(2026,10,1,12,tzinfo=dt_timezone.utc)
    ClassroomNotificationPreference.objects.create(school_id=c[0].id,account=c[2],in_app=True,digest_day=3,timezone='UTC')
    monkeypatch.setattr('academics.family_notifications.timezone.now',lambda:now)
    first=prepare_classroom_notices.run();second=prepare_classroom_notices.run()
    assert first['digest_notices']==1 and second['digest_notices']==0
    assert first['delivery']=='in_app'
    assert ClassroomFamilyNotice.objects.count()==1
    scheduled=settings.CELERY_BEAT_SCHEDULE['classroom-notices-every-15-minutes']
    assert scheduled['task']==prepare_classroom_notices.name


def test_reminders_preserve_preferences_and_deduplicate(classroom):
    c=classroom;now=datetime(2026,10,1,12,tzinfo=dt_timezone.utc)
    guardian=Guardian.objects.get(account=c[2])
    slot=ClassroomConferenceSlot.objects.create(school_id=c[0].id,section=c[5],teacher=c[1],starts_at=now+timedelta(hours=4),ends_at=now+timedelta(hours=4,minutes=20),location='Classroom',state='booked')
    thread=ClassroomFamilyThread.objects.create(school_id=c[0].id,section=c[5],student=c[4],guardian=guardian,created_by=c[2],slot=slot,kind='conference',title='Learning conference')
    ClassroomNotificationPreference.objects.create(school_id=c[0].id,account=c[2],in_app=False)
    assert prepare_conference_reminders(now)==1
    assert prepare_conference_reminders(now)==0
    notice=ClassroomFamilyNotice.objects.get()
    assert notice.account==c[1] and notice.thread==thread
