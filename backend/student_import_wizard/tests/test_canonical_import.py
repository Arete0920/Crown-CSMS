import uuid
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, close_old_connections
from rest_framework.test import APIClient
from core.models import Student, StudentIdentityLink, GradeLevel, CrownPermission, RolePermission
from households.models import Student as CompatibilityStudent
from student_import_wizard.models import StudentImportWizardSession as Session
from student_import_wizard import services
from .test_views import _school, _client, _h, _rows, COLUMN_MAP, BASE_URL

pytestmark = pytest.mark.django_db

@pytest.fixture
def context():
    school=_school(); return school,_client(school)


def post(c, path=BASE_URL, data=None):
    return c[1].post(path,data or {},format='json',**_h(c[0].id))


def staged(c, rows=None, mapping=None):
    session=post(c).data['session_id']
    configured=post(c,f'{BASE_URL}{session}/configure/',{'column_map': mapping or COLUMN_MAP,'staged_rows': rows if rows is not None else _rows(c[0])})
    assert configured.status_code == 200, configured.data
    preview=post(c,f'{BASE_URL}{session}/preview/'); assert preview.status_code == 200,preview.data
    return session,preview.data


def commit(c, session, preview, **extra):
    return post(c,f'{BASE_URL}{session}/commit/',{'confirm':True,'fingerprint':preview['fingerprint'],'reason':'Reviewed synthetic import source',**extra})


def verify(c, session):
    return c[1].get(f'{BASE_URL}{session}/verify/',**_h(c[0].id))


def test_preview_commit_retry_and_actual_canonical_verification(context):
    c=context; session,preview=staged(c)
    assert preview['valid'] == 1 and preview['errors'] == [] and not Student.objects.exists()
    response=commit(c,session,preview); assert response.status_code == 200,response.data
    assert response.data['created'] == 1 and Student.objects.count() == CompatibilityStudent.objects.count() == StudentIdentityLink.objects.count() == 1
    link=StudentIdentityLink.objects.get(); assert link.source == 'import' and str(session) in link.evidence_reference
    assert commit(c,session,preview).data['records'] == response.data['records']
    verified=verify(c,session); assert verified.status_code == 200 and verified.data['verified'] is True and verified.data['verified_count'] == 1
    assert commit(c,session,preview).status_code == 200 and Student.objects.count() == 1


@pytest.mark.parametrize('change', [{'Birth':'invalid'},{'Birth':'2099-01-01'},{'First':''},{'First':'X'*81},
    {'Status':'unknown'},{'Family':str(uuid.uuid4())},{'Household':str(uuid.uuid4())},{'Number':True}])
def test_invalid_rows_never_partially_commit(context,change):
    c=context; rows=_rows(c[0]); rows.append({**rows[0],'Number':'SYNTHETIC-002',**change})
    session,preview=staged(c,rows)
    assert preview['errors'] and commit(c,session,preview).status_code == 409
    assert not Student.objects.exists() and not CompatibilityStudent.objects.exists() and not StudentIdentityLink.objects.exists()


def test_duplicate_numbers_and_unsupported_or_duplicate_columns(context):
    c=context; rows=_rows(c[0]); session,preview=staged(c,rows+deepcopy(rows))
    assert preview['errors'] and commit(c,session,preview).status_code == 409
    for mapping in ({'First':'first_name'}, {**COLUMN_MAP,'Other':'student_number'}, {**COLUMN_MAP,'Secret':'unsupported'}, {'First':[]}):
        assert post(c,f'{BASE_URL}{session}/configure/',{'column_map':mapping,'staged_rows':rows}).status_code == 400
    assert post(c,f'{BASE_URL}{session}/configure/',{'column_map':COLUMN_MAP,'staged_rows':[[]]}).status_code == 400


def test_explicit_grade_code_and_external_identifier_alias(context):
    c=context; grade=GradeLevel.objects.create(school=c[0],code='9',label='Grade 9',sort_order=9)
    mapping={**COLUMN_MAP,'Number':'external_id','Grade':'grade_level'}
    rows=[{**_rows(c[0])[0],'Number':'000123','Grade':'9'}]
    session,preview=staged(c,rows,mapping); assert commit(c,session,preview).status_code == 200
    assert Student.objects.get().student_number == '000123' and Student.objects.get().current_grade_level == grade
    assert CompatibilityStudent.objects.get().grade_level == '9'
    grade.code='10';grade.save(); assert verify(c,session).data['verified'] is False


def test_stale_preview_cannot_overwrite_changed_canonical_data(context):
    c=context; session,preview=staged(c); assert commit(c,session,preview).status_code == 200
    second,review=staged(c)
    student=Student.objects.get();student.first_name='Reviewed correction';student.save()
    assert commit(c,second,review).status_code == 409
    assert Student.objects.get().first_name == 'Reviewed correction' and Student.objects.count() == 1
    assert verify(c,session).data['verified'] is False


def test_reimport_updates_same_identity_and_preserves_unmapped_grade(context):
    c=context; grade=GradeLevel.objects.create(school=c[0],code='9',label='Grade 9',sort_order=9)
    session,preview=staged(c,[{**_rows(c[0])[0],'Grade':'9'}],{**COLUMN_MAP,'Grade':'grade_level'})
    assert commit(c,session,preview).status_code == 200
    original=Student.objects.get().id; rows=[{**_rows(c[0])[0],'First':'Alicia'}]
    second,review=staged(c,rows); result=commit(c,second,review)
    assert result.status_code == 200 and result.data['updated'] == 1 and Student.objects.count() == 1
    assert Student.objects.get().id == original and Student.objects.get().current_grade_level == grade
    assert CompatibilityStudent.objects.get().first_name == 'Alicia' and StudentIdentityLink.objects.count() == 1


def test_existing_identity_conflicts_and_unmapped_household_need_explicit_review(context):
    c=context; rows=_rows(c[0]); household_id=rows[0]['Household']
    legacy=CompatibilityStudent.objects.create(school_id=c[0].id,household_id=household_id,first_name='Alice',last_name='Smith')
    session,preview=staged(c); assert preview['errors'] and commit(c,session,preview).status_code == 409
    mapped=[{**rows[0],'Compatibility':str(legacy.id)}]
    second,review=staged(c,mapped,{**COLUMN_MAP,'Compatibility':'compatibility_student_id'})
    assert commit(c,second,review).status_code == 200 and CompatibilityStudent.objects.count() == 1
    third,conflict=staged(c,[{**rows[0],'Birth':'2015-01-01'}])
    assert conflict['errors'] and commit(c,third,conflict).status_code == 409


def test_persistence_failure_rolls_back_every_row_and_session(context,monkeypatch):
    c=context; rows=_rows(c[0]); rows.append({**rows[0],'Number':'SYNTHETIC-002'})
    session,preview=staged(c,rows); original=CompatibilityStudent.save; count=0
    def failing_save(self,*args,**kwargs):
        nonlocal count
        count+=1
        if count == 2: raise IntegrityError('Synthetic persistence conflict')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(CompatibilityStudent,'save',failing_save)
    assert commit(c,session,preview).status_code == 409
    assert not Student.objects.exists() and not CompatibilityStudent.objects.exists() and not StudentIdentityLink.objects.exists()
    row=Session.objects.get(id=session);assert row.status == 'previewed' and row.commit_result is None


def test_exact_confirmation_reason_and_preview_evidence_required(context):
    c=context; session,preview=staged(c)
    assert commit(c,session,preview,confirm='true').status_code == 400
    assert commit(c,session,preview,reason='').status_code == 400
    assert commit(c,session,preview,fingerprint='stale').status_code == 409
    assert not Student.objects.exists()


def test_terminal_import_evidence_is_retained_and_legacy_results_not_verified(context):
    c=context; session,preview=staged(c); assert commit(c,session,preview).status_code == 200
    assert post(c,f'{BASE_URL}{session}/configure/',{'column_map':COLUMN_MAP,'staged_rows':_rows(c[0])}).status_code == 409
    row=Session.objects.get(id=session); row.commit_result={}
    with pytest.raises(ValidationError): row.save()
    with pytest.raises(ValidationError): row.delete()
    with pytest.raises(ValidationError): Session.objects.filter(id=session).delete()
    with pytest.raises(ValidationError): Session.objects.filter(id=session).update(commit_result={})
    legacy=Session.objects.create(school=c[0],created_by=c[1].handler._force_user,status='committed',commit_result={'created':1,'errors':[]})
    assert verify(c,str(legacy.id)).status_code == 400


def test_school_permissions_and_inactive_actors_fail_closed(context):
    c=context; actor=c[1].handler._force_user
    assert c[1].post(BASE_URL,{},format='json').status_code == 400
    RolePermission.objects.filter(role_code='REGISTRAR',permission__code='rosters.edit').delete()
    assert post(c).status_code == 403
    assert not StudentIdentityLink.objects.exists() and not Session.objects.exists()
    RolePermission.objects.create(role_code='REGISTRAR',permission=CrownPermission.objects.get(code='rosters.edit'))
    actor.is_active=False;actor.save();assert post(c).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_two_school_imports_cannot_duplicate_one_canonical_identity():
    if connection.vendor != 'postgresql': pytest.skip('Requires independent PostgreSQL row locks.')
    school=_school(); first=(school,_client(school)); second=(school,_client(school))
    session_a,preview_a=staged(first); session_b,preview_b=staged(second)
    def run(c,session,preview):
        close_old_connections()
        try: return commit(c,session,preview).status_code
        finally: close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(run,first,session_a,preview_a),pool.submit(run,second,session_b,preview_b)]
        assert sorted(job.result(timeout=30) for job in jobs) == [200,409]
    assert Student.objects.count() == CompatibilityStudent.objects.count() == StudentIdentityLink.objects.count() == 1
