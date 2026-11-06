"""Rehearse the prepared Heritage local stack on a real runner, with evidence.

This probes HTTP availability and role-session creation. It is not a browser
walkthrough or proof that an owner's actual Windows laptop is configured.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("heritage_local_launcher", ROOT / "scripts/demo/start_heritage_local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


FIVE_MODULE_BROWSER_SOURCES = (
    "tests/e2e/sandbox-teacher-attendance-assignment.spec.ts",
    "tests/e2e/summer-camp-local-readback.spec.ts",
    "tests/e2e/diadem-local-pickup.spec.ts",
    "tests/e2e/sandbox-parent-financial-aid-submit.spec.ts",
    "tests/e2e/extended-care-local-custody.spec.ts",
    "tests/e2e/jireh-sgo-local-intake.spec.ts",
    "tests/e2e/heritage-module-responsive.spec.ts",
    "tests/e2e/heritage-presenter-launcher.spec.ts",
    "tests/e2e/heritage-presenter-guided-links.spec.ts",
)
GUIDED_LINK_COUNTS = {
    "school_admin": 10,
    "admissions_director": 5,
    "finance_director": 5,
    "teacher": 7,
    "parent": 8,
    "student": 6,
}

UPSTREAM_BROWSER_CHECKS = (
    "six_role_buyer_browser_routes_and_mobile",
    "teacher_attendance_and_classwork_persist_after_reload",
    "summer_camp_authenticated_browser_save_readback",
    "diadem_signed_staff_browser_release_and_denials",
    "diadem_release_single_audit_and_denial_persistence",
    "fictional_jireh_family_application_browser_submission_and_reload",
)


def require_five_module_browser_sources() -> None:
    missing = [path for path in FIVE_MODULE_BROWSER_SOURCES if not (launcher.FRONTEND / path).is_file()]
    if missing:
        raise RuntimeError("Five-module browser sources are missing: " + ", ".join(missing))


def prepare_five_module_verification(env: dict[str, str], python: Path) -> None:
    """Verify prepared data without reseeding or rotating fictional credentials."""
    launcher.enable_five_module_runtime(env)
    if not (launcher.STATE / "heritage.sqlite3").is_file():
        raise RuntimeError("Five-module verification requires a prepared Heritage SQLite database.")
    if not (launcher.STATE / "sgo-credentials.txt").is_file():
        raise RuntimeError("Prepare fictional SGO credentials through the guarded five-module launcher first.")
    subprocess.run(
        [str(python), str(ROOT / "backend/manage.py"), "five_module_demo_preflight", "--strict"],
        cwd=ROOT, env=env, timeout=120, check=True,
    )


def verify_guided_link_audit(scoped: dict[str, str]) -> int:
    """Reject missing, stale, partial, or failing six-persona browser evidence."""
    directory = Path(scoped["CROWN_PRESENTER_LINK_AUDIT_DIR"])
    source = scoped.get("CROWN_EXPECTED_FRONTEND_SHA")
    count = 0
    for role, expected_links in GUIDED_LINK_COUNTS.items():
        record = directory / f"presenter-links-{role}.json"
        if not record.is_file():
            raise RuntimeError(f"Missing guided presenter link evidence for {role}")
        data = json.loads(record.read_text(encoding="utf-8"))
        if (data.get("result") != "PASS" or data.get("source_sha") != source
                or data.get("role") != role or data.get("expected_links") != expected_links
                or data.get("clicked_links") != expected_links
                or len(data.get("pages", [])) != expected_links
                or data.get("browser_errors") or data.get("server_errors")
                or any(not p.get("requested") or not p.get("observed") or not p.get("heading")
                       for p in data["pages"])):
            raise RuntimeError(f"Guided presenter link evidence is incomplete for {role}")
        count += expected_links
    return count


def complete_five_module_browser_checks(browser_env: dict[str, str], evidence: dict) -> None:
    """Run after the existing #611/#612/#620 proof blocks, preserving each journey."""
    missing = [name for name in UPSTREAM_BROWSER_CHECKS if evidence["checks"].get(name) is not True]
    if missing:
        raise RuntimeError("Five-module upstream browser proof is incomplete: " + ", ".join(missing))
    require_five_module_browser_sources()
    scoped = dict(browser_env)
    scoped.update({
        "CROWN_CARE_LOCAL_E2E": "1", "CROWN_REQUIRE_CARE_BROWSER_PROOF": "1",
        "CROWN_SGO_LOCAL_E2E": "1", "CROWN_REQUIRE_SGO_BROWSER_PROOF": "1",
        "CROWN_SGO_LOCAL_CREDENTIALS": str((launcher.STATE / "sgo-credentials.txt").resolve()),
        "CROWN_LOCAL_PRESENTER_E2E": "1", "CROWN_REQUIRE_LOCAL_PRESENTER_PROOF": "1",
        "CROWN_PRESENTER_LINK_AUDIT_DIR": str(launcher.STATE.resolve()),
    })
    # A successful previous run cannot stand in for this source's browser proof.
    for role in GUIDED_LINK_COUNTS:
        (launcher.STATE / f"presenter-links-{role}.json").unlink(missing_ok=True)
    for sources in (FIVE_MODULE_BROWSER_SOURCES[4:6], FIVE_MODULE_BROWSER_SOURCES[6:]):
        subprocess.run(
            launcher.npm_command() + ["run", "test:e2e", "--", *sources,
                                      "--workers=1", "--reporter=line"],
            cwd=launcher.FRONTEND, env=scoped, timeout=600, check=True,
        )
    evidence["guided_links_clicked"] = verify_guided_link_audit(scoped)
    evidence["checks"]["six_persona_guided_links_clicked_and_verified"] = True
    evidence["checks"]["local_presenter_authenticated_click_path"] = True
    evidence["checks"]["five_module_responsive_real_role_browser_audit"] = True
    evidence["checks"]["extended_care_real_am_pm_browser_custody_and_reload"] = True
    evidence["checks"]["jireh_sgo_independent_partners_submission_correction_and_resubmission"] = True


def require_consumed_presenter_denial(python: Path, env: dict[str, str]) -> None:
    """A generic launch/network failure is not proof of consumed-custody denial."""
    result = subprocess.run(
        [str(python), str(ROOT / "scripts/demo/start_heritage_local.py"), "--daycare-presenter-check"],
        cwd=ROOT, env=env, timeout=120, capture_output=True, text=True,
    )
    records = []
    for line in (result.stdout + result.stderr).splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    if result.returncode != 1 or not any(isinstance(r, dict) and r.get("presenter_entry") == "DENIED"
            and r.get("reason") == "PRESENTER_CUSTODY_CONSUMED" for r in records):
        raise RuntimeError("Consumed presenter replay did not provide the required denial proof.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true', help='Run the full six-persona Playwright buyer journey against the started stack.')
    parser.add_argument('--five-module', action='store_true', help='Require all five real module browser journeys on prepared, exact-source local data.')
    args = parser.parse_args()
    if args.five_module and not args.browser:
        parser.error("--five-module requires --browser")
    state = launcher.STATE
    state.mkdir(parents=True, exist_ok=True)
    evidence = {"source_sha": launcher.source_sha(), "platform": sys.platform, "checks": {}, "result": "FAIL"}
    evidence["evidence_scope"] = "five_module_browser" if args.five_module else "heritage_role_rehearsal"
    evidence["release_certified"] = False
    processes = []
    files = []
    opener = build_opener(ProxyHandler({}))
    try:
        if args.five_module:
            launcher.require_five_module_sources()
            require_five_module_browser_sources()
            launcher.require_fresh_five_module_source(evidence["source_sha"])
        launcher.available_ports()
        env = launcher.local_environment()
        python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        if not python.is_file():
            raise RuntimeError("Run start_heritage_local.py --prepare-only before this rehearsal")
        if args.five_module:
            prepare_five_module_verification(env, python)
            evidence["checks"]["strict_five_module_data_preflight"] = True
        for name, command, cwd in (
            ("backend", [str(python), str(ROOT / "backend/manage.py"), "heritage_runserver", "127.0.0.1:8000", "--noreload"], ROOT),
            ("frontend", launcher.preview_command(), launcher.FRONTEND),
        ):
            log = (state / f"rehearsal-{name}.log").open("w", encoding="utf-8")
            files.append(log)
            processes.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT))
        launcher.wait_ready("http://127.0.0.1:8000/api/v1/sandbox/catalog/", processes[0], timeout=120)
        evidence["checks"]["sandbox_catalog_http_200"] = True
        launcher.wait_ready("http://127.0.0.1:4173/sandbox", processes[1], timeout=120)
        evidence["checks"]["frontend_sandbox_http_200"] = True
        with opener.open("http://127.0.0.1:4173/build.json", timeout=20) as response:
            build_identity = json.load(response)
        if build_identity.get("build_sha") != evidence["source_sha"]:
            raise RuntimeError("Heritage frontend build SHA differs from the checked-out source")
        evidence["checks"]["frontend_build_matches_source"] = True
        session_tokens = {}
        for role in ("school_admin", "admissions_director", "finance_director", "parent", "teacher", "student"):
            payload = json.dumps({"role": role, "school": "heritage-core"}).encode("utf-8")
            request = Request(
                "http://127.0.0.1:8000/api/v1/sandbox/session/",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with opener.open(request, timeout=20) as response:
                body = json.load(response)
                if response.status != 201 or not body.get("access") or not body.get("school_id"):
                    raise RuntimeError(f"{role} session response was incomplete")
            session_tokens[role] = (body["access"], body["school_id"])
            evidence["checks"][f"{role}_session_201"] = True
        # Verify the actual finance API authorization boundary, not just session issuance.
        for role, expected_status in (("finance_director", 200), ("parent", 403), ("teacher", 403)):
            access, school_id = session_tokens[role]
            request = Request(
                "http://127.0.0.1:8000/api/v1/billing/invoices/",
                headers={"Authorization": f"Bearer {access}", "X-School-Id": school_id},
            )
            try:
                with opener.open(request, timeout=20) as response:
                    status = response.status
            except HTTPError as exc:
                status = exc.code
            if status != expected_status:
                raise RuntimeError(f"{role} billing authorization returned {status}; expected {expected_status}")
            evidence["checks"][f"{role}_billing_{expected_status}"] = True

        # Board is an additional least-privilege API persona, separate from the
        # six buyer walkthrough personas. Never add it to the browser role set.
        board_request = Request(
            "http://127.0.0.1:8000/api/v1/sandbox/session/",
            data=json.dumps({"role": "board", "school": "heritage-core"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with opener.open(board_request, timeout=20) as response:
            board_session = json.load(response)
            if response.status != 201:
                raise RuntimeError("Board session issuance did not return 201")
        if (
            board_session.get("role_code") != "board_member"
            or not board_session.get("access")
            or board_session.get("school_id") != session_tokens["school_admin"][1]
        ):
            raise RuntimeError("Heritage Board session has an unexpected role or school identity")
        board_headers = {
            "Authorization": f"Bearer {board_session['access']}",
            "X-School-Id": board_session["school_id"],
        }
        for route in (
            "/api/v1/nav/",
            "/api/signals/board/risk-counts/",
            "/api/v1/academics/classroom/workspace/?audience=board",
        ):
            with opener.open(Request("http://127.0.0.1:8000" + route, headers=board_headers), timeout=20) as response:
                if response.status != 200:
                    raise RuntimeError(f"Board permitted read failed: {route} returned {response.status}")
                if route.endswith("audience=board"):
                    aggregate = json.load(response)
                    if any(
                        key in aggregate
                        for key in ("students", "assignments", "lesson_plans", "categories", "sections")
                    ):
                        raise RuntimeError("Board classroom aggregate exposed protected individual records")
                if route == "/api/v1/nav/":
                    nav = json.load(response)
                    links = {
                        item.get("href")
                        for group in nav.get("groups", [])
                        for item in group.get("items", [])
                    }
                    if "/board" not in links or links.intersection({"/admin", "/finance", "/billing"}):
                        raise RuntimeError("Board navigation exposes an incorrect authority set")
        for route in (
            "/api/v1/academics/classroom/workspace/?audience=admin",
            "/api/v1/admin/metrics/",
            "/api/v1/finance/metrics/",
            "/api/v1/sandbox/admin/state/",
            "/api/v1/sandbox/finance/state/",
        ):
            try:
                with opener.open(Request("http://127.0.0.1:8000" + route, headers=board_headers), timeout=20) as response:
                    actual = response.status
            except HTTPError as exc:
                actual = exc.code
            if actual != 403:
                raise RuntimeError(f"Board forbidden read was not denied: {route} returned {actual}")
        evidence["checks"]["board_own_school_and_least_privilege"] = True
        if args.browser:
            browser_env = dict(env)
            browser_env["CROWN_LIVE_FRONTEND_URL"] = "http://localhost:4173"
            browser_env["CROWN_BROWSER_AUTHORITY_OUTPUT"] = str(state / "buyer-browser-authority.json")
            subprocess.run(
                launcher.npm_command() + ["run", "certify:buyer-sandbox-browser"],
                cwd=launcher.FRONTEND, env=browser_env, timeout=1200, check=True,
            )
            browser_report = state / "buyer-browser-authority.json"
            if not browser_report.is_file():
                raise RuntimeError("Buyer browser certification did not produce its evidence file")
            report = json.loads(browser_report.read_text(encoding="utf-8"))
            if report.get("testSourceSha") != evidence["source_sha"]:
                raise RuntimeError("Buyer browser evidence source differs from the prepared application")
            personas = {item.get("persona") for item in report.get("results", [])}
            required = set(session_tokens)
            if not required.issubset(personas):
                raise RuntimeError(f"Buyer browser certification omitted roles: {sorted(required - personas)}")
            evidence["checks"]["six_role_buyer_browser_routes_and_mobile"] = True
            evidence["browser_route_count"] = report.get("routeCount")

            # Reuse the existing real-browser attendance/classwork regression.
            # A saved response alone cannot certify that reload restored the mark.
            browser_env["CERT_FRONTEND_URL"] = "http://127.0.0.1:4173"
            # This stack already has a Vite preview on :4173. Without live
            # certification mode, Playwright's CI webServer attempts to start
            # another preview on the occupied port and fails before testing.
            browser_env["CROWN_CERTIFICATION_LIVE_RUNTIME"] = "1"
            browser_env["CROWN_EXPECTED_FRONTEND_SHA"] = evidence["source_sha"]
            subprocess.run(
                launcher.npm_command() + [
                    "run", "test:e2e", "--",
                    "tests/e2e/sandbox-teacher-attendance-assignment.spec.ts",
                    "tests/e2e/sandbox-parent-financial-aid-submit.spec.ts",
                    "--workers=1", "--reporter=line",
                ],
                cwd=launcher.FRONTEND, env=browser_env, timeout=600, check=True,
            )
            evidence["checks"]["teacher_attendance_and_classwork_persist_after_reload"] = True
            evidence["checks"]["fictional_jireh_family_application_browser_submission_and_reload"] = True

            # Real Camp role session, persisted POST/GET/read-after-reload, and
            # controlled failure cases. The spec restores prior fictional state.
            browser_env["CROWN_LOCAL_CAMP_E2E"] = "1"
            subprocess.run(
                launcher.npm_command() + [
                    "run", "test:e2e", "--",
                    "tests/e2e/summer-camp-local-readback.spec.ts",
                    "--workers=1", "--reporter=line",
                ],
                cwd=launcher.FRONTEND, env=browser_env, timeout=600, check=True,
            )
            evidence["checks"]["summer_camp_authenticated_browser_save_readback"] = True
            # Actual authenticated Diadem pickup: fictional local SQLite only.
            # No browser API stubs; one signed staff identity exercises real custody.
            # The explicit presenter owns exclusive first-use preparation. Never
            # overwrite its existing manifest by running the ordinary seeder here.
            browser_env["CROWN_DIADEM_PICKUP_MANIFEST"] = str(state / "diadem-pickup-session.json")
            # Exercise the actual human command, including Django source/identity
            # guards and visible Windows Chromium, before the custody journey.
            subprocess.run([str(python), str(ROOT / "scripts/demo/start_heritage_local.py"),
                            "--daycare-presenter-check"], cwd=ROOT, env=env, check=True, timeout=120)
            evidence["checks"]["diadem_private_staff_presenter_browser_entry"] = True
            browser_env["CROWN_REQUIRE_DIADEM_PICKUP_PROOF"] = "1"
            subprocess.run(
                launcher.npm_command() + [
                    "run", "test:e2e", "--",
                    "tests/e2e/diadem-local-pickup.spec.ts",
                    "--workers=1", "--reporter=line",
                ],
                cwd=launcher.FRONTEND, env=browser_env, timeout=600, check=True,
            )
            require_consumed_presenter_denial(python, env)
            evidence["checks"]["diadem_consumed_presenter_replay_denied"] = True
            subprocess.run(
                [str(python), str(ROOT / "backend/manage.py"), "seed_local_diadem_pickup", "--verify"],
                cwd=ROOT, env=env, timeout=120, check=True,
            )
            evidence["checks"]["diadem_signed_staff_browser_release_and_denials"] = True
            evidence["checks"]["diadem_release_single_audit_and_denial_persistence"] = True
        if args.five_module:
            complete_five_module_browser_checks(browser_env, evidence)
            evidence["five_module_browser_passed"] = True
        evidence["result"] = "PASS"
        if args.five_module:
            print("Five-module Heritage browser acceptance passed. Package/source identity and owner release certification remain separate gates.")
        else:
            print("Heritage Windows runner rehearsal passed: exact local build, frontend, backend, six buyer sessions, Board least privilege, and finance denials." + (" Full buyer browser and teacher attendance/classwork reload certification passed." if args.browser else " Browser journey not executed."))
        return 0
    except Exception as exc:
        evidence["error"] = str(exc)
        print(f"Heritage runner rehearsal failed: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            launcher.stop(process)
        for handle in files:
            handle.close()
        (state / "rehearsal-result.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
