"""Private presenter guards; mocked readbacks are not Windows browser evidence."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from django.core.management.base import CommandError
from rest_framework_simplejwt.tokens import AccessToken
from sandbox_demo.management.commands import seed_local_diadem_pickup as pickup

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
SCHOOL = "19801b59-8c05-4c84-9312-5d792e4e839d"
ID = "11111111-1111-4111-8111-111111111111"


class PrivateScenario(dict):
    def __repr__(self):
        return "<private fictional staff scenario>"


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    monkeypatch.setattr(pickup, "MANIFEST", tmp_path / "private.json")
    monkeypatch.setattr(pickup, "require_local_demo", lambda: None)
    monkeypatch.setattr(pickup.local_launcher, "require_presenter_preparation", lambda: None)
    monkeypatch.setattr(pickup.local_launcher, "source_sha", lambda: SHA)
    monkeypatch.setenv("BUILD_SHA", SHA)
    for key in ("WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "AZURE_CLIENT_ID"):
        monkeypatch.delenv(key, raising=False)
    token = AccessToken()
    token["user_id"], token["school_id"] = "synthetic-user", SCHOOL
    data = PrivateScenario(fictional_only=True, source_sha=SHA, school_id=SCHOOL, scenario="a" * 10,
                site_id=ID, staff_access=str(token),
                cases={"approved": {"attendance_id": ID, "authority_id": ID}})
    pickup.MANIFEST.write_text(json.dumps(data))
    roles = SimpleNamespace(filter=lambda **kw: SimpleNamespace(exists=lambda: True))
    user = SimpleNamespace(school_id=SCHOOL, school=object(), roles=roles)
    monkeypatch.setattr(pickup.JWTAuthentication, "get_user", lambda *args: user)
    monkeypatch.setattr(pickup, "user_has_permission", lambda *a, **kw: True)
    monkeypatch.setattr(pickup, "build_scenario", lambda: pytest.fail("No existing scenario reset"))
    return data, user


def test_existing_session_is_reused_without_file_or_credential_change(scenario):
    before = pickup.MANIFEST.read_bytes()
    assert pickup.presenter_scenario() == scenario[0]
    assert pickup.presenter_scenario() == scenario[0]
    assert pickup.MANIFEST.read_bytes() == before


@pytest.mark.parametrize("mutation", ["source", "checkout", "tenant", "token-tenant", "expired", "parent", "admin", "permission", "hosted", "malformed", "symlink"])
def test_presenter_rejects_stale_forbidden_or_ambiguous_identity(scenario, monkeypatch, mutation):
    data, user = scenario
    if mutation == "source": data["source_sha"] = "b" * 40
    if mutation == "checkout": monkeypatch.setattr(pickup.local_launcher, "source_sha", lambda: "b" * 40)
    if mutation == "tenant": user.school_id = "other-school"
    if mutation in {"parent", "admin"}:
        user.roles = SimpleNamespace(filter=lambda **kw: SimpleNamespace(exists=lambda: False))
    if mutation == "permission": monkeypatch.setattr(pickup, "user_has_permission", lambda *a, **kw: False)
    if mutation in {"expired", "token-tenant"}:
        token = AccessToken(data["staff_access"])
        token["exp" if mutation == "expired" else "school_id"] = 1 if mutation == "expired" else "other-school"
        data["staff_access"] = str(token)
    if mutation == "hosted": monkeypatch.setenv("WEBSITE_HOSTNAME", "example.azurewebsites.net")
    pickup.MANIFEST.write_text("invalid" if mutation == "malformed" else json.dumps(data))
    if mutation == "symlink":
        target = pickup.MANIFEST.with_name("other.json")
        pickup.MANIFEST.rename(target)
        pickup.MANIFEST.symlink_to(target)
    before = pickup.MANIFEST.read_bytes()
    with pytest.raises(CommandError): pickup.presenter_scenario()
    assert pickup.MANIFEST.read_bytes() == before


def test_nonlocal_database_is_denied_before_manifest_io(monkeypatch):
    def denied(): raise CommandError("Nonlocal database denied")
    monkeypatch.setattr(pickup, "_require_isolated_local_database", denied)
    with pytest.raises(CommandError, match="Nonlocal database"): pickup.presenter_scenario()


def test_new_presenter_reserves_once_without_overwriting_failed_or_existing_state(scenario, monkeypatch):
    data, _ = scenario
    pickup.MANIFEST.unlink()
    calls = []
    def create():
        calls.append(True)
        assert pickup.MANIFEST.is_file()
        return data
    monkeypatch.setattr(pickup, "build_scenario", create)
    assert pickup.presenter_scenario() == data
    assert pickup.presenter_scenario() == data
    assert len(calls) == 1
    pickup.MANIFEST.write_text("")
    with pytest.raises(CommandError): pickup.presenter_scenario()
    assert len(calls) == 1


@pytest.mark.parametrize("failure", ["none", "frontend", "backend", "hosted", "anonymous", "released", "guardian"])
def test_node_preflight_requires_source_authenticated_roster_and_current_guardian(scenario, failure):
    script = ROOT / "frontend/dashboards/scripts/heritage-daycare-presenter.mjs"
    program = '''
      import assert from 'node:assert/strict';
      const {verifyPresenter} = await import(process.argv[1]);
      let input=''; for await (const chunk of process.stdin) input+=chunk;
      const {scenario:s, sha, failure:f}=JSON.parse(input); const calls=[];
      const fake=async (url, options)=>{
        calls.push({url,options}); assert.equal(options.redirect,'error');
        const body=url.endsWith('/build.json')?{build_sha:f==='frontend'?'wrong':sha}:
          url.endsWith('/api/health/')?{build_sha:f==='backend'?'wrong':sha,env:f==='hosted'?'dev':'local',db:'ok'}:
          url.endsWith('/roster/')?{site_id:s.site_id,rows:f==='released'?[]:[{attendance_id:s.cases.approved.attendance_id}]}:
          {attendance_id:s.cases.approved.attendance_id,options:f==='guardian'?[]:[{authority_id:s.cases.approved.authority_id}]};
        return {status:f==='anonymous'&&options.headers.Authorization?403:200,json:async()=>body};
      };
      if(f==='none') {await verifyPresenter(s,sha,fake); assert.equal(calls.length,4);
        for(const c of calls.slice(2)) assert.equal(c.options.headers.Authorization,'Bearer '+s.staff_access);
      } else await assert.rejects(verifyPresenter(s,sha,fake));
    '''
    result = subprocess.run(["node", "--input-type=module", "-e", program, script.as_uri()],
                            input=json.dumps({"scenario": scenario[0], "sha": SHA, "failure": failure}),
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_presenter_command_uses_private_stdin_not_argv_or_environment(scenario, monkeypatch):
    calls = []
    monkeypatch.setattr(pickup.shutil, "which", lambda name: "/local/node")
    monkeypatch.setattr(pickup.subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)))
    pickup.Command().handle(presenter=True, verify=False)
    command, options = calls[0]
    assert len(command) == 2 and command[-1].endswith("heritage-daycare-presenter.mjs")
    assert json.loads(options["input"]) == scenario[0]
    assert options["check"] and options["text"] and "env" not in options
    assert scenario[0]["staff_access"] not in str(command)


def test_cli_failure_never_prints_private_manifest_or_token(scenario):
    data = dict(scenario[0], source_sha="invalid")
    env = dict(os.environ, BUILD_SHA=SHA)
    result = subprocess.run(["node", str(ROOT / "frontend/dashboards/scripts/heritage-daycare-presenter.mjs")],
                            input=json.dumps(data), env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 1
    assert "Presenter entry refused" in result.stderr
    assert data["staff_access"] not in result.stdout + result.stderr


def test_entry_does_not_reinstall_authentication_or_clear_custody_guards_on_reload(scenario):
    program = '''
      import assert from 'node:assert/strict';
      const {enterPresenter}=await import(process.argv[1]);
      let text='';for await(const chunk of process.stdin)text+=chunk;
      const {scenario:s,sha}=JSON.parse(text); let installs=0;
      globalThis.fetch=async url=>({status:200,json:async()=>url.endsWith('/build.json')?{build_sha:sha}:
        url.endsWith('/api/health/')?{build_sha:sha,env:'local',db:'ok'}:
        url.endsWith('/roster/')?{site_id:s.site_id,rows:[{attendance_id:s.cases.approved.attendance_id}]}:
        {attendance_id:s.cases.approved.attendance_id,options:[{authority_id:s.cases.approved.authority_id}]}});
      globalThis.location={origin:'http://127.0.0.1:4173'};
      const storage=new Map();globalThis.sessionStorage={clear:()=>storage.clear(),setItem:(k,v)=>storage.set(k,v)};
      const page={goto:async()=>({status:()=>200,json:async()=>({build_sha:sha})}),
        evaluate:async(fn,arg)=>{installs++;fn(arg)},getByRole:()=>({waitFor:async()=>{}}),
        addInitScript:()=>assert.fail('No persistent auth reinstall hook')};
      await enterPresenter(page,s,sha);assert.equal(storage.get('crown.jwt.access'),s.staff_access);
      storage.set('crown.extended-care.unconfirmed-custody','pending');
      await page.goto('/reload');assert.equal(installs,1);
      assert.equal(storage.get('crown.extended-care.unconfirmed-custody'),'pending');
    '''
    result = subprocess.run(["node", "--input-type=module", "-e", program,
                             (ROOT / "frontend/dashboards/scripts/heritage-daycare-presenter.mjs").as_uri()],
                            input=json.dumps({"scenario": scenario[0], "sha": SHA}), text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("failure", ["hosted", "unprepared", "stale"])
def test_launcher_refuses_presenter_before_local_keys_or_processes(monkeypatch, tmp_path, failure):
    spec = importlib.util.spec_from_file_location("presenter_launcher", ROOT / "scripts/demo/start_heritage_local.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    monkeypatch.setattr(launcher, "source_sha", lambda: SHA)
    monkeypatch.setattr(launcher, "local_environment", lambda: pytest.fail("No credential mutation"))
    if failure == "hosted": monkeypatch.setenv("WEBSITE_INSTANCE_ID", "hosted")
    if failure == "stale":
        (tmp_path / "heritage.sqlite3").touch()
        for name in ("seed.complete", "relationships.complete"): (tmp_path / name).write_text("b" * 40)
    with pytest.raises(RuntimeError): launcher.daycare_presenter()


@pytest.mark.django_db
def test_real_signed_staff_entry_release_and_independent_api_readback(monkeypatch, tmp_path, settings):
    """Real JWT and API/DB proof on pytest SQLite, not canonical-path/Chromium certification."""
    from uuid import uuid4
    from rest_framework.test import APIClient
    from core.models import School, UserAccount, UserRole
    from aftercare.models import DaycareRelease
    from audit.models import AuditLog
    settings.DEBUG, settings.CROWN_ENV = True, "local"
    monkeypatch.setattr(pickup, "require_local_demo", lambda: None)
    monkeypatch.setattr(pickup.local_launcher, "require_presenter_preparation", lambda: None)
    monkeypatch.setattr(pickup.local_launcher, "source_sha", lambda: SHA)
    monkeypatch.setattr(pickup, "MANIFEST", tmp_path / "private-session.json")
    monkeypatch.setenv("BUILD_SHA", SHA)
    School.objects.create(id=SCHOOL, name="Heritage Christian Academy", timezone="America/New_York", is_active=True)
    data = pickup.presenter_scenario()
    before = pickup.MANIFEST.read_bytes()
    assert pickup.presenter_scenario() == data
    url = "/api/v1/aftercare/daycare/sites/" + data["site_id"] + "/roster/"
    def client(token=None, school=SCHOOL):
        result = APIClient()
        result.credentials(**({"HTTP_AUTHORIZATION": "Bearer " + token, "HTTP_X_SCHOOL_ID": school} if token else {}))
        return result
    staff = client(data["staff_access"])
    assert staff.get(url).status_code == 200
    assert client().get(url).status_code in (401, 403)
    assert client(data["unprivileged_access"]).get(url).status_code == 403
    assert client(data["staff_access"], str(uuid4())).get(url).status_code in (403, 404)
    admin = UserAccount.objects.create_user(username="synthetic-presenter-admin", school_id=SCHOOL)
    UserRole.objects.create(user=admin, school_id=SCHOOL, role_code="HEAD_OF_SCHOOL")
    assert client(pickup.local_token(admin, admin.school)).get(url).status_code == 403
    expired = AccessToken(data["staff_access"])
    expired["exp"] = 1
    assert client(str(expired)).get(url).status_code == 401
    release_url = "/api/v1/aftercare/daycare/attendance/release/"
    def release(case):
        return dict(site_id=data["site_id"], room_id=data["room_id"], attendance_id=case["attendance_id"],
                    guardian_authority_id=case["authority_id"], request_key=str(uuid4()),
                    identity_method="GOVERNMENT_PHOTO_ID", identity_verified=True)
    for kind in ("revoked", "expired"):
        assert staff.post(release_url, release(data["cases"][kind]), format="json").status_code == 400
    payload = release(data["cases"]["approved"])
    response = staff.post(release_url, payload, format="json")
    assert response.status_code == 201
    assert staff.post(release_url, payload, format="json").status_code == 409
    saved = client(data["staff_access"]).get(url)
    assert saved.status_code == 200
    assert data["cases"]["approved"]["attendance_id"] not in {row["attendance_id"] for row in saved.json()["rows"]}
    assert DaycareRelease.objects.count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.release").count() == 1
    assert pickup.MANIFEST.read_bytes() == before
