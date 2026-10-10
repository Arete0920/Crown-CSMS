"""Rehearse the prepared Heritage local stack on a real runner, with evidence.

This probes HTTP availability and role-session creation. It is not a browser
walkthrough or proof that an owner's actual Windows laptop is configured.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("heritage_local_launcher", ROOT / "scripts/demo/start_heritage_local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def main() -> int:
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
        for role in ("school_admin", "parent", "teacher", "student"):
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
            evidence["checks"][f"{role}_session_201"] = True
        evidence["result"] = "PASS"
        print("Heritage Windows runner rehearsal passed: frontend, backend, four role sessions.")
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
