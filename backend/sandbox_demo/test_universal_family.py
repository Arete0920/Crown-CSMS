"""Actual student submission -> teacher grading -> family readback."""
from decimal import Decimal
import os

import pytest
from django.core.management.base import CommandError

from academics.models import Assignment, Grade, Submission, SubmissionRevision
from core.models import StudentIdentityLink
from sandbox_demo.test_universal_access import local_runtime, operator_secrets, login
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID

pytestmark = pytest.mark.django_db


def test_normal_roles_submit_grade_and_read_the_same_persisted_family_record(local_runtime, operator_secrets):
    data = prepare_presenter(apply=True, enable_password_login=True)
    teacher, _ = login("teacher", operator_secrets)
    student, _ = login("student", operator_secrets)
    parent, _ = login("parent", operator_secrets)
    link = StudentIdentityLink.objects.get(school_id=UNIVERSAL_SCHOOL_ID,
                                           core_student_id=data["family_student_id"])
    assert str(link.compatibility_student_id) == data["family_student_id"]
    created = teacher.post(f"/api/v1/academics/sections/{data['family_section_id']}/assignments/", {
        "name": "Fictional narrative assessment", "category_id": data["family_category_id"],
        "points_possible": "20", "is_published": True,
    }, format="json")
    assert created.status_code == 201, created.content
    assignment = created.json()["id"]
    submit_url = "/api/v1/academics/submissions/"
    payload = {"assignment": assignment, "enrollment": data["family_enrollment_id"]}
    assert parent.post(submit_url, payload, format="json").status_code == 403
    submitted = student.post(submit_url, payload, format="json")
    assert submitted.status_code == 201, submitted.content
    submission = Submission.objects.get(school_id=UNIVERSAL_SCHOOL_ID, assignment_id=assignment)
    assert submission.submitted_at and submission.status == Submission.Status.SUBMITTED
    grade_url = "/api/v1/academics/grades/grade/"
    grade_payload = {"submission_id": str(submission.pk), "numeric_score": "18", "teacher_feedback": "Evidence and explanation"}
    assert student.post(grade_url, grade_payload, format="json").status_code == 403
    assert parent.post(grade_url, grade_payload, format="json").status_code == 403
    graded = teacher.post(grade_url, grade_payload, format="json")
    assert graded.status_code == 200, graded.content
    assert Grade.objects.get(submission=submission).percentage == Decimal("90.00")
    submission.refresh_from_db()
    assert submission.status == Submission.Status.GRADED
    assert SubmissionRevision.objects.filter(submission=submission, action="graded").count() == 1
    for role in ("parent", "student"):
        reader, _ = login(role, operator_secrets)
        result = reader.get("/api/v1/academics/classroom/workspace/", {"audience": role})
        assert result.status_code == 200, result.content
        rows = [row for row in result.json()["assignments"] if row["id"] == assignment]
        assert len(rows) == 1
        assert rows[0]["state"] == "graded"
        assert Decimal(str(rows[0]["points_earned"])) == Decimal("18")
    # Existing academic history is append-only. A safe reset must refuse this
    # state rather than delete a grade's protected audit lineage to pass a demo.
    with pytest.raises(CommandError, match="protected relationships"):
        prepare_presenter(apply=True, reset=True)
    assert Assignment.objects.filter(pk=assignment).exists()
    assert SubmissionRevision.objects.filter(submission=submission).count() == 1
    assert Grade.objects.get(submission=submission).percentage == Decimal("90.00")
    from sandbox_demo.universal_family import archive_presenter_classroom
    from core.models import UserAccount
    credentials = dict(UserAccount.objects.filter(school_id=UNIVERSAL_SCHOOL_ID).values_list("id", "password"))
    assert archive_presenter_classroom()["assignments_archived"] == 1
    assert archive_presenter_classroom()["assignments_archived"] == 0
    assert parent.get("/api/v1/academics/classroom/workspace/", {"audience": "parent"}).json()["assignments"] == []
    assert SubmissionRevision.objects.filter(submission=submission).count() == 1
    assert dict(UserAccount.objects.filter(school_id=UNIVERSAL_SCHOOL_ID).values_list("id", "password")) == credentials


@pytest.mark.skipif(os.environ.get('CROWN_RUN_UNIVERSAL_BROWSER') != '1', reason='Explicit disposable local browser harness only')
@pytest.mark.django_db(transaction=True)
def test_normal_browser_workflow(live_server, local_runtime, operator_secrets, settings, tmp_path):
    import json
    from pathlib import Path
    import subprocess
    import time
    import urllib.request
    from core.models import School
    from sandbox_demo.universal_identity import presenter_username
    root = Path(__file__).resolve().parents[2]
    frontend = root / 'frontend/dashboards'
    assert live_server.url == 'http://127.0.0.1:8004'
    settings.CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:4178']
    settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
    data = prepare_presenter(apply=True, enable_password_login=True)
    for _ in range(2):
        data = prepare_presenter(apply=True, reset=True, enable_password_login=True)
    foreign = School.objects.create(name='Separate fictional browser-denial school')
    assert (frontend / 'dist/index.html').exists(), 'Build the normal-login frontend before this test'
    output = root / '.local-backups/universal-demo/browser-evidence.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    settings.BUILD_SHA = source
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip())
    fixture = {'synthetic': True, 'api': live_server.url, 'frontend': 'http://127.0.0.1:4178',
               'school_id': data['school_id'], 'foreign_school_id': str(foreign.pk),
               'source_sha': source, 'source_dirty': dirty,
               'usernames': {key: presenter_username(key) for key in operator_secrets}, 'passwords': operator_secrets}
    env = {**os.environ, 'CROWN_UNIVERSAL_BROWSER_FIXTURE': json.dumps(fixture),
           'CROWN_UNIVERSAL_BROWSER_OUTPUT': str(output)}
    if Path('/usr/bin/chromium').exists():
        env['CROWN_BROWSER_EXECUTABLE'] = '/usr/bin/chromium'
    def wait_preview(preview):
        for attempt in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:4178/login', timeout=1).close()
                break
            except OSError:
                if preview.poll() is not None:
                    pytest.fail('Local preview exited before browser acceptance')
                time.sleep(0.1)
        else:
            pytest.fail('Local preview did not become ready')
    with (tmp_path / 'preview.log').open('w') as log:
        preview = subprocess.Popen(['node', 'node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4178', '--strictPort'], cwd=frontend, stdout=log, stderr=log)
        try:
            wait_preview(preview)
            result = subprocess.run(['node', 'scripts/universal-presenter-acceptance.mjs'], cwd=frontend, env=env, capture_output=True, text=True, timeout=240)
            assert preview.poll() is None, "Owned frontend preview exited"
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            preview.terminate()
            preview.wait(timeout=15)
    evidence = json.loads(output.read_text())
    submission = Submission.objects.get(school_id=UNIVERSAL_SCHOOL_ID, assignment_id=evidence['assignment_id'])
    assert submission.submitted_at
    assert SubmissionRevision.objects.filter(submission=submission, action='save_draft').count() == 1
    assert SubmissionRevision.objects.filter(submission=submission, action='submit').count() == 1
    assert SubmissionRevision.objects.filter(submission=submission, action='feedback').count() == 1

    from sandbox_demo.universal_family import archive_presenter_classroom
    assert archive_presenter_classroom()["assignments_archived"] == 1
    assert archive_presenter_classroom()["assignments_archived"] == 0
    fixture["verify_archived"] = True
    fixture["assignment_id"] = evidence["assignment_id"]
    archived_output = tmp_path / "archived-browser.json"
    env.update(CROWN_UNIVERSAL_BROWSER_FIXTURE=json.dumps(fixture), CROWN_UNIVERSAL_BROWSER_OUTPUT=str(archived_output))
    with (tmp_path / "archive-preview.log").open("w") as log:
        preview = subprocess.Popen(['node', 'node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4178', '--strictPort'], cwd=frontend, stdout=log, stderr=log)
        try:
            wait_preview(preview)
            result = subprocess.run(['node', 'scripts/universal-presenter-acceptance.mjs'], cwd=frontend, env=env, capture_output=True, text=True, timeout=120)
            assert preview.poll() is None, "Owned frontend preview exited"
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            preview.terminate()
            preview.wait(timeout=15)
    evidence["checks"].extend(json.loads(archived_output.read_text())["checks"])
    evidence["immutable_history_retained"] = SubmissionRevision.objects.filter(submission=submission).count() == 3
    assert evidence["immutable_history_retained"]
    output.write_text(json.dumps(evidence, indent=2))


def test_classroom_archive_preserves_foreign_records_and_refuses_unsafe_runtime(local_runtime, settings, django_assert_num_queries):
    from academics.models import AssignmentCategory, Course, Section
    from core.models import School
    from sandbox_demo.universal_family import archive_presenter_classroom
    prepare_presenter(apply=True)
    foreign = School.objects.create(name='Other fictional archival school')
    course = Course.objects.create(school_id=foreign.pk, code='OTHER', name='Other course')
    section = Section.objects.create(school_id=foreign.pk, course=course, term='2026-FALL')
    category = AssignmentCategory.objects.create(school_id=foreign.pk, section=section, name='Other category')
    assignment = Assignment.objects.create(school_id=foreign.pk, section=section, category=category, name='Preserve published foreign work', points_possible=10)
    assert archive_presenter_classroom()['assignments_archived'] == 0
    assignment.refresh_from_db()
    assert assignment.is_published
    settings.CROWN_ENV = 'production'
    with django_assert_num_queries(0), pytest.raises(CommandError):
        archive_presenter_classroom()
