from datetime import timedelta
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection, close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from audit.models import AuditLog
from comms.models import ContentRelease, OutboxMessage, ReleaseReceipt
from comms.release_services import activate_due_releases, preview, publish, render_email
from comms.tasks import drain_outbox
from core.models import School
from households.models import Guardian, Household, Student
from onboarding.models_tasks import HelpArticle
from reenrollment.models import ReenrollmentSession


@pytest.fixture
def setup(db):
    school = School.objects.create(name='Release School')
    owner = get_user_model().objects.create_user(username='owner', email='owner@example.com', school=school, is_superuser=True)
    parent = get_user_model().objects.create_user(username='parent', email='parent@example.com', school=school)
    household = Household.objects.create(school_id=school.pk, name='Family')
    guardian = Guardian.objects.create(school_id=school.pk, household=household, account=parent, first_name='Parent', last_name='One', email='parent@example.com')
    student = Student.objects.create(school_id=school.pk, household=household, first_name='Student', last_name='One')
    session = ReenrollmentSession.objects.create(school=school, created_by=owner, target_year_label='2027-2028', status='configured', deadline_at=timezone.now() + timedelta(days=30), candidates_snapshot=[{'id': str(student.pk), 'household_id': str(household.pk)}])
    release = ContentRelease.objects.create(session=session, owner=owner, title='Re-enrollment', blocks=[{'type': 'action', 'title': 'Your plans', 'body': 'Please respond.', 'link': '/parent/admissions/status'}])
    client = APIClient()
    client.force_authenticate(owner)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.pk))
    return school, owner, parent, guardian, student, session, release, client


def approve(release):
    data = preview(release)
    release.status = 'approved'
    release.approved_fingerprint = data['fingerprint']
    release.approved_by = release.owner
    release.save()
    return data


def action(client, release, name, **kwargs):
    return client.post(f'/api/comms/releases/{release.pk}/{name}/', {'revision': release.revision, **kwargs}, format='json')


@pytest.mark.django_db
def test_complete_preview_approval_publication_family_response(setup):
    school, owner, parent, guardian, student, session, release, client = setup
    response = action(client, release, 'preview')
    assert response.status_code == 200
    assert response.data['recipients'] == 1
    assert 'audience' not in response.data
    assert action(client, release, 'approve', fingerprint=response.data['fingerprint']).status_code == 200
    assert action(client, release, 'publish').status_code == 200
    assert action(client, release, 'publish').status_code == 200
    assert OutboxMessage.objects.count() == ReleaseReceipt.objects.count() == 1
    client.force_authenticate(parent)
    feed = client.get('/api/comms/family-releases/')
    assert feed.status_code == 200 and feed.data[0]['deadline'] == response.data['deadline']
    assert client.post(f'/api/comms/family-releases/{release.pk}/respond/', {'response': 'returning'}, format='json').status_code == 200
    assert ReleaseReceipt.objects.get().response == 'returning'
    assert AuditLog.objects.filter(action='content.family_response').exists()


@pytest.mark.django_db
@pytest.mark.parametrize('change', ['deadline', 'selection', 'email', 'account', 'resource'])
def test_dependency_drift_blocks_publication(setup, change):
    school, owner, parent, guardian, student, session, release, client = setup
    if change == 'resource':
        article = HelpArticle.objects.create(slug='guide', title='Guide', content='Original', module='reenrollment')
        release.blocks[0]['resource_slug'] = 'guide'
        release.save()
    approve(release)
    if change == 'deadline':
        session.deadline_at += timedelta(days=1)
        session.save()
    elif change == 'selection':
        student.is_active = False
        student.save()
    elif change == 'email':
        guardian.email = 'changed@example.com'
        guardian.save()
    elif change == 'account':
        parent.is_active = False
        parent.save()
    else:
        article.content = 'Changed'
        article.save()
    with pytest.raises(ValidationError):
        publish(release.pk)
    assert not OutboxMessage.objects.exists()


@pytest.mark.django_db
def test_edit_invalidates_approval_and_stale_revision_fails(setup):
    *_, release, client = setup
    approve(release)
    content = {'title': 'Changed', 'blocks': release.blocks}
    assert action(client, release, 'update', content=content).status_code == 200
    assert action(client, release, 'approve', fingerprint='old').status_code == 409
    release.refresh_from_db()
    assert release.status == 'draft' and not release.approved_fingerprint
    assert action(client, release, 'publish').status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('block', [
    {'type': 'raw', 'title': 'x', 'body': 'x'},
    {'type': 'action', 'title': 'x', 'body': 'x', 'link': 'javascript:alert(1)'},
    {'type': 'action', 'title': 'x', 'body': 'x', 'link': '//evil.example'},
    {'type': 'action', 'title': 'x', 'body': 'x', 'link': '/\\evil.example'},
    {'type': 'action', 'title': 'x', 'body': 'x', 'recipient': 'someone@example.com'},
])
def test_model_and_api_reject_unsafe_blocks(setup, block):
    *_, release, client = setup
    release.blocks = [block]
    with pytest.raises(ValidationError):
        release.save()
    response = client.post(f'/api/comms/releases/session/{release.session_id}/', {'title': 'x', 'blocks': [block]}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_render_escapes_markup_and_private_resources_rejected(setup):
    *_, release, client = setup
    release.blocks[0]['body'] = '<script>bad()</script>'
    release.save()
    assert '<script>' not in render_email(preview(release))
    HelpArticle.objects.create(slug='private', title='Private', content='Sensitive', module='reenrollment', visibility='admin')
    release.blocks[0]['resource_slug'] = 'private'
    release.save()
    assert action(client, release, 'preview').status_code == 400


@pytest.mark.django_db
def test_schedule_expiry_and_blocked_schedule(setup):
    *_, release, client = setup
    release.publish_at = timezone.now() + timedelta(hours=1)
    release.expires_at = timezone.now() + timedelta(hours=2)
    release.save()
    approve(release)
    assert activate_due_releases()['published'] == 0
    assert action(client, release, 'publish').status_code == 400
    with patch('comms.release_services.timezone.now', return_value=timezone.now() + timedelta(hours=1, minutes=1)):
        assert activate_due_releases()['published'] == 1
    client.force_authenticate(setup[2])
    with patch('comms.release_api.timezone.now', return_value=timezone.now() + timedelta(hours=3)):
        assert client.get('/api/comms/family-releases/').data == []


@pytest.mark.django_db
def test_scheduled_drift_becomes_visible_blocker(setup):
    *_, release, client = setup
    release.publish_at = timezone.now() - timedelta(minutes=1)
    release.save()
    approve(release)
    setup[5].deadline_at += timedelta(days=1)
    setup[5].save()
    assert activate_due_releases() == {'published': 0, 'blocked': 1}
    release.refresh_from_db()
    assert release.status == 'draft' and release.last_error and not release.approved_by


@pytest.mark.django_db
def test_cross_school_and_non_manager_denied(setup):
    school, owner, parent, guardian, student, session, release, client = setup
    client.force_authenticate(parent)
    assert action(client, release, 'preview').status_code == 403
    other = School.objects.create(name='Other')
    client.force_authenticate(owner)
    client.credentials(HTTP_X_SCHOOL_ID=str(other.pk))
    assert action(client, release, 'preview').status_code == 404
    client.force_authenticate(None)
    assert client.get('/api/comms/family-releases/').status_code in (400, 401, 403)


@pytest.mark.django_db
def test_other_guardian_cannot_read_or_acknowledge(setup):
    *_, release, client = setup
    approve(release)
    publish(release.pk)
    user = get_user_model().objects.create_user(username='unrelated', email='unrelated@example.com', school=setup[0])
    household = Household.objects.create(school_id=setup[0].pk, name='Other family')
    Guardian.objects.create(school_id=setup[0].pk, household=household, account=user, first_name='Other', last_name='Parent')
    client.force_authenticate(user)
    assert client.get('/api/comms/family-releases/').data == []
    assert client.post(f'/api/comms/family-releases/{release.pk}/respond/', {'response': 'returning'}, format='json').status_code == 404


@pytest.mark.django_db
def test_correction_and_atomic_rollback(setup):
    *_, release, client = setup
    approve(release)
    with patch('comms.release_services.audit', side_effect=RuntimeError('audit unavailable')):
        with pytest.raises(RuntimeError):
            publish(release.pk)
    assert not OutboxMessage.objects.exists() and not ReleaseReceipt.objects.exists()
    publish(release.pk)
    release.refresh_from_db()
    with pytest.raises(ValidationError):
        release.save()
    correction = ContentRelease.objects.create(session=release.session, owner=release.owner, title='Corrected', blocks=release.blocks, supersedes=release)
    approve(correction)
    publish(correction.pk)
    client.force_authenticate(setup[2])
    assert [r['id'] for r in client.get('/api/comms/family-releases/').data] == [str(correction.pk)]


@pytest.mark.django_db
@pytest.mark.parametrize('fee', ['NaN', 'Infinity', '1.001', '100000000'])
def test_invalid_billing_fee_fails_closed(setup, fee):
    *_, release, client = setup
    response = client.post(f'/api/v1/reenrollment/sessions/{release.session_id}/configure/', {'target_year_label': '2027', 'enrollment_fee': fee}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_billing_commit_cannot_be_reconfigured_or_repeated_after_verify(setup):
    *_, release, client = setup
    base = f'/api/v1/reenrollment/sessions/{release.session_id}/'
    assert client.post(base + 'commit/', {'confirm': 'false'}, format='json').status_code == 400
    assert client.post(base + 'commit/', {'confirm': True}, format='json').status_code == 200
    assert client.post(base + 'configure/', {'target_year_label': '2028', 'enrollment_fee': '1'}, format='json').status_code == 409
    assert client.get(base + 'verify/').status_code == 200
    assert client.post(base + 'commit/', {'confirm': True}, format='json').data['already_committed']


@pytest.mark.django_db(transaction=True)
def test_postgresql_workers_do_not_send_same_message_concurrently(setup):
    if connection.vendor != 'postgresql':
        pytest.skip('PostgreSQL row-lock proof requires PostgreSQL')
    *_, release, client = setup
    approve(release)
    publish(release.pk)
    started, finish = Event(), Event()
    calls = []
    def send(message):
        calls.append(str(message.pk))
        started.set()
        assert finish.wait(10)
    def drain():
        close_old_connections()
        try:
            return drain_outbox.run(batch_size=1)
        finally:
            close_old_connections()
    with patch('comms.tasks._send', side_effect=send), ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(drain)
        try:
            assert started.wait(10)
            second = pool.submit(drain)
            assert second.result(timeout=10)['sent'] == 0
        finally:
            finish.set()
        assert first.result(timeout=10)['sent'] == 1
    assert len(calls) == 1


@pytest.mark.django_db
def test_deadline_edit_preserves_billing_and_requires_new_preview(setup):
    *_, release, client = setup
    approve(release)
    original = preview(release)['fingerprint']
    deadline = timezone.now() + timedelta(days=45)
    response = client.post(f'/api/comms/releases/session/{release.session_id}/deadline/', {'deadline_at': deadline.isoformat(), 'communication_timezone': 'America/New_York'}, format='json')
    assert response.status_code == 200
    release.refresh_from_db()
    assert preview(release)['fingerprint'] != original
    assert action(client, release, 'publish').status_code == 400
    assert release.session.enrollment_fee == setup[5].enrollment_fee


@pytest.mark.django_db
def test_preferences_and_no_portal_account_are_reported_truthfully(setup):
    from comms.models import NotificationPreference
    from comms.release_services import metrics
    *_, release, client = setup
    NotificationPreference.objects.create(user=setup[2], email_enabled=False)
    approve(release)
    publish(release.pk)
    assert not OutboxMessage.objects.exists()
    result = metrics(release)
    assert result['recipients'] == result['portal_available'] == 1
    assert result['email_delivery_confirmed'] is None and result['enrollment_completed'] is None


@pytest.mark.django_db
def test_invalid_schedule_and_model_cross_school_guard(setup):
    *_, release, client = setup
    release.publish_at = timezone.now() + timedelta(days=2)
    release.expires_at = timezone.now() + timedelta(days=1)
    with pytest.raises(ValidationError):
        release.save()
    other = School.objects.create(name='Cross School')
    household = Household.objects.create(school_id=other.pk, name='Other')
    guardian = Guardian.objects.create(school_id=other.pk, household=household, first_name='Other', last_name='Guardian')
    with pytest.raises(ValidationError):
        ReleaseReceipt.objects.create(release=setup[6], guardian=guardian)


@pytest.mark.django_db
@pytest.mark.parametrize('timestamp', ['2027-03-01T08:00:00', 'bad-date'])
def test_naive_or_invalid_schedule_rejected_by_api(setup, timestamp):
    *_, release, client = setup
    response = client.post(f'/api/comms/releases/session/{release.session_id}/', {'title': 'Notice', 'blocks': release.blocks, 'publish_at': timestamp}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_session_creation_rejects_parent_without_edit_permission(setup):
    school, owner, parent, guardian, student, session, release, client = setup
    client.force_authenticate(parent)
    before = ReenrollmentSession.objects.count()
    assert client.post('/api/v1/reenrollment/sessions/', {}, format='json').status_code == 403
    assert ReenrollmentSession.objects.count() == before
