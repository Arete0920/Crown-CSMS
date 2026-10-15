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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true', help='Run the full six-persona Playwright buyer journey against the started stack.')
    args = parser.parse_args()
    state = launcher.STATE
    state.mkdir(parents=True, exist_ok=True)
    evidence = {"source_sha": launcher.source_sha(), "platform": sys.platform, "checks": {}, "result": "FAIL"}
    processes = []
    files = []
    opener = build_opener(ProxyHandler({}))
    try:
        launcher.available_ports()
        env = launcher.local_environment()
        python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        if not python.is_file():
            raise RuntimeError("Run start_heritage_local.py --prepare-only before this rehearsal")
        for name, command, cwd in (
            ("backend", [str(python), str(ROOT / "backend/manage.py"), "runserver", "127.0.0.1:8000", "--noreload"], ROOT),
            ("frontend", launcher.preview_command(), launcher.FRONTEND),
        ):
            log = (state / f"rehearsal-{name}.log").open("w", encoding="utf-8")
            files.append(log)
            processes.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT))
        launcher.wait_ready("http://127.0.0.1:8000/api/v1/sandbox/catalog/", processes[0], timeout=120)
        evidence["checks"]["sandbox_catalog_http_200"] = True
        launcher.wait_ready("http://127.0.0.1:4173/sandbox", processes[1], timeout=120)
        evidence["checks"]["frontend_sandbox_http_200"] = True
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
            personas = {item.get("persona") for item in report.get("results", [])}
            required = set(session_tokens)
            if not required.issubset(personas):
                raise RuntimeError(f"Buyer browser certification omitted roles: {sorted(required - personas)}")
            evidence["checks"]["six_role_buyer_browser_routes_and_mobile"] = True
            evidence["browser_route_count"] = report.get("routeCount")
        evidence["result"] = "PASS"
        print("Heritage Windows runner rehearsal passed: frontend, backend, six role sessions, and finance denials." + (" Full buyer browser certification passed." if args.browser else " Browser journey not executed."))
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
