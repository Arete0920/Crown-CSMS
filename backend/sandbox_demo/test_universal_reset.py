"""Retained-history reset with actual logins, transactions, replay and isolation."""
from io import StringIO
from uuid import UUID, uuid4
from unittest.mock import patch
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole
from aid.models import AidApplication
from aftercare.models import DaycareAttendance
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID, presenter_username, generation_school, GENERATION_EVENT
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_care import prepare_presenter_care
from sandbox_demo.universal_jireh import prepare_presenter_jireh
from sandbox_demo.universal_admissions import prepare_presenter_admissions
from sandbox_demo.universal_reset import rollover_presenter
from sandbox_demo.egress import sandbox_external_egress_blocked
from sandbox_demo.models import SandboxEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def ready(local_runtime, operator_secrets):
    call_command('seed_permissions', stdout=StringIO())
    prepare_presenter(apply=True, enable_password_login=True)
    care = prepare_presenter_care(apply=True)
    prepare_presenter_jireh(apply=True)
    prepare_presenter_admissions(apply=True)
    return care


def _new_parent(school_id, passwords):
    client = APIClient()
    response = client.post('/api/v1/auth/token/', {'username': presenter_username('parent', school_id),
        'password': passwords['parent']}, format='json')
    assert response.status_code == 200, response.content
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.json()['access'], HTTP_X_SCHOOL_ID=str(school_id))
    return client


def _submit_aid(client):
    url = '/api/v1/presenter/jireh/aid/family/'
    data = client.get(url).json()
    response = client.post(url, {'fictional_acknowledged': True, 'scenario': data['scenarios'][0]['id'],
        'household_size': 4, 'academic_year_id': data['academic_years'][0]['id'],
        'student_ids': [data['students'][0]['id']]}, format='json')
    assert response.status_code == 201, response.content
    return response.json()['application']['id']


def test_two_rollovers_replay_real_workflow_preserve_history_and_revoke_old_login(ready, operator_secrets, settings):
    old_parent, _ = login('parent', operator_secrets)
    old_app = _submit_aid(old_parent)
    from core.models import RolePermission
    global_grants = set(RolePermission.objects.values_list("role_code", "permission_id"))
    old_hashes = dict(UserAccount.objects.values_list('pk', 'password'))
    foreign = School.objects.create(id='19801b59-8c05-4c84-9312-5d792e4e839d', name='Heritage Christian Academy')
    current = UNIVERSAL_SCHOOL_ID
    for number in (1, 2):
        key = uuid4()
        preflight = rollover_presenter(expected_current=current, request_key=key)
        assert preflight['mode'] == 'PREFLIGHT'
        before = School.objects.count()
        result = rollover_presenter(expected_current=current, request_key=key, apply=True, enable_password_login=True)
        assert result['mode'] == 'ROLLED_OVER' and result['generation'] == number
        assert School.objects.count() == before + 1
        retry = rollover_presenter(expected_current=current, request_key=key, apply=True, enable_password_login=True)
        assert retry['mode'] == 'ALREADY_APPLIED' and School.objects.count() == before + 1
        assert not School.objects.get(pk=current).is_active
        current = UUID(result['school_id'])
        assert str(current) == generation_school(number).id
        new_parent = _new_parent(current, operator_secrets)
        assert new_parent.get('/api/v1/presenter/jireh/aid/family/').json()['applications'] == []
        _submit_aid(new_parent)
        with pytest.raises(CommandError, match='Stale'):
            rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    assert AidApplication.objects.filter(pk=old_app, school_id=UNIVERSAL_SCHOOL_ID).exists()
    assert AidApplication.objects.count() == 3
    assert global_grants == set(RolePermission.objects.values_list("role_code", "permission_id"))
    denied_login = APIClient().post('/api/v1/auth/token/', {'username': presenter_username('parent'),
        'password': operator_secrets['parent']}, format='json')
    assert denied_login.status_code == 401
    assert not UserAccount.objects.filter(school_id=UNIVERSAL_SCHOOL_ID, is_active=True).exists()
    assert old_parent.get('/api/v1/presenter/jireh/aid/family/').status_code == 404  # Retired tenant is unavailable before endpoint authorization.
    assert dict(UserAccount.objects.filter(pk__in=old_hashes).values_list('pk', 'password')) == old_hashes
    assert School.objects.get(pk=foreign.pk).is_active
    assert not UserAccount.objects.filter(school=foreign).exists()
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    assert sandbox_external_egress_blocked(school_id=current)
    unscoped = UserAccount.objects.create(username='fictional-role-only-reset-user', school=None)
    UserRole.objects.create(user=unscoped, school_id=current, role_code='PARENT')
    assert sandbox_external_egress_blocked(sender=unscoped)


def test_unresolved_custody_blocks_retirement_and_preserves_active_accounts(ready, operator_secrets):
    staff, _ = login('daycare_staff', operator_secrets)
    admitted = staff.post('/api/v1/aftercare/daycare/attendance/checkin/', {
        **{key: ready[key] for key in ('site_id', 'room_id', 'child_id')},
        'program_code': 'DAYCARE', 'request_key': str(uuid4())}, format='json')
    assert admitted.status_code == 201, admitted.content
    with pytest.raises(CommandError, match='unresolved custody'):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    assert School.objects.count() == 1 and School.objects.get().is_active
    assert UserAccount.objects.filter(is_active=True).count() == 9 and DaycareAttendance.objects.count() == 1


def test_foreign_role_or_reserved_id_collision_never_changes_another_school(ready):
    foreign = School.objects.create(name='Independent foreign-role school')
    user = UserAccount.objects.get(username=presenter_username('teacher'))
    role = UserRole.objects.create(user=user, school=foreign, role_code='TEACHER')
    with pytest.raises(CommandError, match='foreign or unscoped'):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    role.delete()
    collision = School.objects.create(id=generation_school(1).id, name='Reserved collision must not be adopted')
    with pytest.raises(CommandError, match='already exists'):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    assert School.objects.get(pk=collision.pk).name == collision.name
    assert School.objects.get(pk=UNIVERSAL_SCHOOL_ID).is_active
    assert UserAccount.objects.get(pk=user.pk).is_active


def test_partial_generation_failure_rolls_back_retirement_and_all_new_records(ready):
    before = dict(UserAccount.objects.values_list('pk', 'password'))
    with patch('sandbox_demo.universal_reset.prepare_presenter_jireh', side_effect=CommandError('synthetic generation rollback')):
        with pytest.raises(CommandError, match='generation rollback'):
            rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    assert School.objects.count() == 1 and School.objects.get().is_active
    assert not SandboxEvent.objects.filter(event=GENERATION_EVENT).exists()
    assert before == dict(UserAccount.objects.values_list('pk', 'password'))
    assert UserAccount.objects.filter(is_active=True).count() == 9


def test_invalid_runtime_and_request_key_refuse_before_queries(local_runtime, settings, django_assert_num_queries):
    with django_assert_num_queries(0), pytest.raises(CommandError):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key='not-a-key')
    settings.CROWN_ENV = 'production'
    with django_assert_num_queries(0), pytest.raises(CommandError):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('admission_first', [True, False])
def test_postgresql_admission_and_reset_serialize(settings, operator_secrets, admission_first):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from django.db import connection, close_old_connections, transaction
    if connection.vendor != 'postgresql':
        pytest.skip('Actual PostgreSQL row locking required; SQLite is not concurrency proof.')
    from aftercare.services import checkin_student, school_local_date
    from households.models import Student as PortalStudent
    from sandbox_demo.universal_demo import _prepare_presenter, _owned_school
    from sandbox_demo.universal_access import presenter_passwords
    from sandbox_demo.universal_reset import _assert_no_open_custody
    settings.CROWN_ENV = 'dev'
    settings.DEBUG = False
    settings.CROWN_DEMO_MODE = False
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
    # Only the cloud runtime predicate is mocked, never DB locks or services.
    # The DB is the CI PostgreSQL service; no Azure connection is made.
    with patch('sandbox_demo.universal_runtime.require_hosted_presenter'):
        call_command('seed_permissions', stdout=StringIO())
        _prepare_presenter(apply=True, reset=False, passwords=presenter_passwords())
        care = prepare_presenter_care(apply=True)
        prepare_presenter_jireh(apply=True)
        prepare_presenter_admissions(apply=True)
        assert connection.in_atomic_block is False
        assert _owned_school().pk == UNIVERSAL_SCHOOL_ID
        parent = _new_parent(UNIVERSAL_SCHOOL_ID, operator_secrets)
        _submit_aid(parent)
        first_locked, second_ready, proceed = Event(), Event(), Event()
        def admit():
            close_old_connections()
            try:
                with transaction.atomic():
                    if admission_first:
                        PortalStudent.objects.select_for_update().get(pk=care['care_student_id'])
                        first_locked.set()
                        assert proceed.wait(20), 'Reset never acquired its root lock'
                    return checkin_student(UNIVERSAL_SCHOOL_ID, UUID(care['care_student_id']), care_session='AM').pk
            finally:
                connection.close()
        def reset():
            close_old_connections()
            try:
                return rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID,
                    request_key=uuid4(), apply=True, enable_password_login=True)
            finally:
                connection.close()
        def root_locked():
            school = _owned_school()
            second_ready.set()
            return school
        def children_locked(school):
            _assert_no_open_custody(school)
            first_locked.set()
            assert proceed.wait(20), 'Admission never reached the active-child fence'
        def school_read(school_id, at):
            day = school_local_date(school_id, at)
            second_ready.set()
            return day
        with ThreadPoolExecutor(max_workers=2) as pool:
            if admission_first:
                admit_result = pool.submit(admit)
                assert first_locked.wait(20)
                with patch('sandbox_demo.universal_reset._owned_school', side_effect=root_locked):
                    reset_result = pool.submit(reset)
                    assert second_ready.wait(20)
                    proceed.set()
                    assert admit_result.result(timeout=30)
                    with pytest.raises(CommandError, match='unresolved custody'):
                        reset_result.result(timeout=30)
                assert School.objects.get(pk=UNIVERSAL_SCHOOL_ID).is_active
            else:
                with patch('sandbox_demo.universal_reset._assert_no_open_custody', side_effect=children_locked):
                    reset_result = pool.submit(reset)
                    assert first_locked.wait(20)
                    with patch('aftercare.services.school_local_date', side_effect=school_read):
                        admit_result = pool.submit(admit)
                        assert second_ready.wait(20)
                        proceed.set()
                        result = reset_result.result(timeout=60)
                        assert result['mode'] == 'ROLLED_OVER'
                        with pytest.raises(ValueError, match='not active'):
                            admit_result.result(timeout=30)
                assert not School.objects.get(pk=UNIVERSAL_SCHOOL_ID).is_active
                from aftercare.models import AftercareAttendance
                assert not AftercareAttendance.objects.filter(school_fk_id=UNIVERSAL_SCHOOL_ID).exists()


def test_retention_capacity_is_a_hard_refusal_not_history_deletion(ready):
    with patch('sandbox_demo.universal_reset.MAX_GENERATION', 0), pytest.raises(CommandError, match='capacity reached'):
        rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(), apply=True, enable_password_login=True)
    assert School.objects.count() == 1 and UserAccount.objects.filter(is_active=True).count() == 9
