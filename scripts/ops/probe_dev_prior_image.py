"""Probe one recorded DEV image on the current job's disposable PG15 copy.

No Azure calls, arbitrary images, live DB selectors, volumes, or host ports.
This limited probe is not full application rollback or durable recovery proof.
"""
from __future__ import annotations

import json
import re
import secrets
import subprocess

PRIOR_SHA = "2c77580df6676ebfb5580b2d3924897ff33125ee"
PRIOR_IMAGE = ("crownregistry.azurecr.io/crown2026@sha256:"
               "b4586bafd87113b3cb3e6c4df9b1792e683c2ded636c08ef57881c6fc18492cb")
CONFIRMATION = "test-prior-image-on-disposable-copy"
DOCKER = ["docker", "--host", "unix:///var/run/docker.sock"]


class PriorImageBlocked(RuntimeError):
    """Only fixed reason codes may leave this helper."""


def validate_scope(container, database, cluster, source_sha, environ):
    run_id, attempt = environ.get("GITHUB_RUN_ID", ""), environ.get("GITHUB_RUN_ATTEMPT", "")
    if (environ.get("GITHUB_ACTIONS") != "true"
            or environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or environ.get("GITHUB_REF") != "refs/heads/main"
            or environ.get("GITHUB_REPOSITORY") != "Arete0920/Crown-CSMS"
            or environ.get("GITHUB_REPOSITORY_ID") != "1339719218"
            or environ.get("GITHUB_SHA") != source_sha
            or not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha)
            or not isinstance(container, str) or not re.fullmatch(r"[0-9a-f]{12,64}", container)
            or environ.get("POSTGRES_CONTAINER_ID") != container
            or not re.fullmatch(r"[0-9]{1,20}", run_id)
            or not re.fullmatch(r"[0-9]{1,5}", attempt)
            or database != f"crown_restore_{run_id}_{attempt}"
            or not isinstance(cluster, str) or not re.fullmatch(r"[0-9]{1,24}", cluster)):
        raise PriorImageBlocked("prior_image_disposable_scope_denied")


def process_environment(environ):
    # The Docker client can use its existing ephemeral registry auth. None of
    # that configuration, source credentials or Azure identity enters the app.
    return {key: environ[key] for key in ("PATH", "HOME", "DOCKER_CONFIG") if key in environ}


def app_environment(database, cluster):
    return {
        "DATABASE_URL": f"postgresql://crown_drill:crown-drill-password@127.0.0.1:5432/{database}?sslmode=disable",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "DJANGO_SETTINGS_MODULE": "crown_api.settings", "CROWN_ENV": "dev",
        "DJANGO_ENV": "development", "ENVIRONMENT": "dev", "DEBUG": "false",
        "DJANGO_DEBUG": "false", "ALLOWED_HOSTS": "127.0.0.1,localhost",
        "BUILD_SHA": PRIOR_SHA, "PORT": "8000", "WEBSITES_PORT": "8000",
        "CROWN_SIMPLEJWT_BLACKLIST_ENABLED": "false", "CROWN_DEMO_MODE": "false",
        "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "false", "BOOTSTRAP_ADMIN": "false",
        "SEED_DEMO": "false", "RUN_DEV_BOOTSTRAP": "0", "RUN_GOLDEN_PATH_BOOTSTRAP": "0",
        "CROWN_PRIOR_IMAGE_DATABASE": database, "CROWN_PRIOR_IMAGE_CLUSTER": cluster,
        "HTTP_PROXY": "", "HTTPS_PROXY": "", "ALL_PROXY": "", "NO_PROXY": "127.0.0.1,localhost",
        "http_proxy": "", "https_proxy": "", "all_proxy": "", "no_proxy": "127.0.0.1,localhost",
    }


# Runs inside the actual digest-pinned old image, not with today's model code.
# Rows and exceptions stay private. Every test INSERT is rolled back.
PROBE = r'''
import json, os, time, urllib.request, urllib.error
stage = ["prior_image_private_execution_failed"]
def probe():
    import django
    django.setup()
    from django.db import connection, transaction
    from django.apps import apps
    stage[0] = "prior_image_database_identity_failed"
    expected = os.environ["CROWN_PRIOR_IMAGE_DATABASE"]
    if (connection.vendor != "postgresql" or connection.settings_dict["HOST"] != "127.0.0.1"
            or str(connection.settings_dict.get("PORT") or "5432") != "5432"
            or connection.settings_dict["NAME"] != expected):
        return "prior_image_database_identity_failed"
    with connection.cursor() as c:
        c.execute("SELECT current_database(),current_user,current_setting('server_version_num')::int")
        db, user, version = c.fetchone()
        c.execute("SELECT system_identifier FROM pg_control_system()")
        cluster = str(c.fetchone()[0])
    if (db != expected or user != "crown_drill" or version // 10000 != 15
            or cluster != os.environ["CROWN_PRIOR_IMAGE_CLUSTER"]):
        return "prior_image_database_identity_failed"
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    stage[0] = "prior_image_startup_or_artifact_failed"
    healthy = False
    for _ in range(45):
        try:
            with opener.open("http://127.0.0.1:8000/api/health/", timeout=2) as r:
                data = json.loads(r.read(16384))
                healthy = (r.status == 200 and data.get("db") == "ok" and data.get("env") == "dev"
                           and data.get("build_sha") == os.environ["BUILD_SHA"]
                           and data.get("artifact_build_sha") == os.environ["BUILD_SHA"])
            if healthy: break
        except Exception: pass
        time.sleep(1)
    if not healthy: return "prior_image_startup_or_artifact_failed"
    stage[0] = "prior_image_anonymous_denial_failed"
    for path in ("/api/platform/overview", "/api/platform/schools/list"):
        try:
            with opener.open("http://127.0.0.1:8000" + path, timeout=5) as r:
                status = r.status
        except urllib.error.HTTPError as e: status = e.code
        if status not in (401, 403): return "prior_image_anonymous_denial_failed"
    from datetime import date, datetime, time as clock
    from django.utils import timezone
    from uuid import uuid4
    stage[0] = "prior_image_legacy_insert_failed"
    School = apps.get_model("core", "School")
    Attendance = apps.get_model("aftercare", "AftercareAttendance")
    before = (School.objects.count(), Attendance.objects.count())
    with transaction.atomic():
        school = School.objects.create(name="Fictional prior-image compatibility probe")
        household = apps.get_model("households", "Household").objects.create(school_id=school.pk, name="Fictional Probe")
        child = apps.get_model("households", "Student").objects.create(
            school_id=school.pk, household=household, first_name="Fictional", last_name="Probe", grade_level="4")
        attendance = Attendance.objects.create(school_fk_id=school.pk, student_fk_id=child.pk,
            date=date(2025,9,4), checkin_time=timezone.make_aware(datetime(2025,9,4,15)), pickup_verified=False)
        if not Attendance.objects.filter(pk=attendance.pk, school_fk_id=school.pk).exists():
            raise AssertionError("legacy_insert_readback_failed")
        apps.get_model("aftercare", "AftercareProgramConfig").objects.create(school_fk_id=school.pk)
        apps.get_model("aftercare", "AftercareEnrollment").objects.create(
            school_fk_id=school.pk, student_fk_id=child.pk, start_date=date(2025,9,4), billing_model="FLAT_MONTHLY")
        user = apps.get_model("core", "UserAccount").objects.create(
            school_id=school.pk, username="fictional-prior-"+uuid4().hex, email=uuid4().hex+"@example.invalid", password="!")
        program = apps.get_model("summer_camp", "SummerCampProgram").objects.create(school_id=school.pk,name="Fictional Probe")
        session = apps.get_model("summer_camp", "SummerCampSession").objects.create(
            school_id=school.pk,program=program,name="Fictional Probe",start_date=date(2025,7,1),end_date=date(2025,7,2),
            start_time=clock(8),end_time=clock(15))
        apps.get_model("summer_camp", "SummerCampStaffAssignment").objects.create(
            school_id=school.pk,session=session,staff_user=user,role="Fictional probe",credential_status="PENDING")
        transaction.set_rollback(True)
    if before != (School.objects.count(), Attendance.objects.count()):
        return "prior_image_probe_rows_not_rolled_back"
    return None
try:
    reason = probe()
except Exception:
    reason = stage[0]
print(json.dumps({"result":"BLOCKED", "reason":reason} if reason else {"result":"PASS"}))
raise SystemExit(1 if reason else 0)
'''

SAFE_REASONS = frozenset({
    "prior_image_database_identity_failed", "prior_image_startup_or_artifact_failed",
    "prior_image_anonymous_denial_failed", "prior_image_legacy_insert_failed",
    "prior_image_probe_rows_not_rolled_back", "prior_image_private_execution_failed",
})


def verify_disposable_target(container, database, cluster, environ):
    from dev_backup_restore import target_environment, target_identity, scalar
    try:
        env = target_environment(environ)
        target_identity(container, env, expected_major=15)
        if (scalar(container, env, database, "SELECT current_database()") != database
                or scalar(container, env, database,
                          "SELECT system_identifier FROM pg_control_system()") != cluster):
            raise PriorImageBlocked("prior_image_disposable_target_unverified")
    except Exception:
        raise PriorImageBlocked("prior_image_disposable_target_unverified") from None


def probe_prior_image(container, database, cluster, source_sha, environ, *,
                      run=subprocess.run, verify_target=verify_disposable_target):
    validate_scope(container, database, cluster, source_sha, environ)
    verify_target(container, database, cluster, environ)  # Before pull or startup.
    client_env = process_environment(environ)
    app_env = app_environment(database, cluster)
    ownership = secrets.token_hex(10)
    name = "crown-prior-probe-" + ownership

    def invoke(args, *, env=client_env, stdin=None, timeout=180):
        try:
            return run(DOCKER + args, env=env, input=stdin, capture_output=True,
                       text=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise PriorImageBlocked("prior_image_process_unavailable") from None

    if invoke(["pull", PRIOR_IMAGE]).returncode:
        raise PriorImageBlocked("prior_image_pull_unavailable")
    inspected = invoke(["image", "inspect", "--format", "{{json .RepoDigests}}", PRIOR_IMAGE])
    try:
        digests = json.loads(inspected.stdout)
    except (ValueError, TypeError):
        digests = None
    if inspected.returncode or not isinstance(digests, list) or PRIOR_IMAGE not in digests:
        raise PriorImageBlocked("prior_image_digest_unverified")
    args = ["run", "--detach", "--name", name, "--label", "crown.prior-probe=" + ownership,
            "--pull=never",
            "--network", "container:" + container, "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
            "--memory=768m", "--cpus=1", "--pids-limit=128", "--log-driver=none"]
    for key in sorted(app_env):
        args += ["--env", key]  # Synthetic values/signing key stay off argv.
    attempted = False
    try:
        attempted = True
        if invoke(args + [PRIOR_IMAGE], env={**client_env, **app_env}).returncode:
            raise PriorImageBlocked("prior_image_container_start_failed")
        result = invoke(["exec", "-i", name, "python", "-"], stdin=PROBE)
        try:
            lines = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
        except (ValueError, TypeError):
            lines = []
        receipt = lines[0] if len(lines) == 1 else {}
        if result.returncode or receipt != {"result": "PASS"}:
            reason = receipt.get("reason") if isinstance(receipt, dict) else None
            raise PriorImageBlocked(reason if isinstance(reason, str) and reason in SAFE_REASONS
                                    else "prior_image_probe_receipt_invalid")
    finally:
        if attempted:
            # Even an uncertain failed start must never remove an unrelated
            # preexisting container that happened to occupy the requested name.
            owned = invoke(["container", "inspect", "--format", "{{json .Config.Labels}}", name])
            try:
                labels = json.loads(owned.stdout)
            except (ValueError, TypeError):
                labels = None
            if (owned.returncode or not isinstance(labels, dict)
                    or labels.get("crown.prior-probe") != ownership):
                raise PriorImageBlocked("prior_image_container_cleanup_unverified")
            if invoke(["rm", "--force", name]).returncode:
                raise PriorImageBlocked("prior_image_container_cleanup_failed")
    return {"result": "PASS", "source_sha": source_sha, "prior_image": PRIOR_IMAGE,
            "prior_source_sha": PRIOR_SHA, "startup_and_artifact_verified": True,
            "anonymous_platform_denied": True, "rolled_back_legacy_inserts_verified": True,
            "probe_container_removed": True, "live_schema_write_performed": False,
            "scope": "startup_anonymous_denial_and_rolled_back_legacy_inserts",
            "full_application_rollback": "NOT_VERIFIED"}
