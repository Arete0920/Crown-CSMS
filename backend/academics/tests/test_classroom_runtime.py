"""Run classroom notice preparation through a real local Celery worker."""
import pytest
from datetime import timedelta
from celery import Celery
from celery.contrib.testing.worker import start_worker
from django.conf import settings
from django.utils import timezone
from academics.tests.test_classroom_experience import classroom
from academics.family_models import ClassroomNotificationPreference, ClassroomFamilyNotice
from academics.tasks import prepare_family_notices


@pytest.mark.django_db(transaction=True)
def test_worker_prepares_scheduled_notices_and_repeated_delivery_is_safe(classroom):
    c = classroom
    ClassroomNotificationPreference.objects.create(school_id=c[0].id, account=c[2], in_app=True,
        digest_day=timezone.now().weekday(), timezone='UTC')
    entry = settings.CELERY_BEAT_SCHEDULE['classroom-family-notices-every-15-minutes']
    assert entry['task'] == prepare_family_notices.name
    assert entry['schedule'].is_due(timezone.now()-timedelta(minutes=16)).is_due
    with Celery('classroom_runtime', broker='memory://', backend='cache+memory://', set_as_current=False) as app:
        app.task(name=prepare_family_notices.name)(prepare_family_notices.run)
        with start_worker(app, pool='solo', concurrency=1, perform_ping_check=False, shutdown_timeout=10):
            first = app.send_task(entry['task']).get(timeout=15)
            second = app.send_task(entry['task']).get(timeout=15)
        assert first['digests'] == 1 and second['digests'] == 0
        assert ClassroomFamilyNotice.objects.filter(source_key__startswith='digest:').count() == 1
