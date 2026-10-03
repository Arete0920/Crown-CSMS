"""Start the isolated, passwordless Heritage demo on this computer."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import ProxyHandler, build_opener
import venv
import webbrowser

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".local-backups" / "heritage-demo"
FRONTEND = ROOT / "frontend" / "dashboards"
URL = "http://localhost:4173/sandbox"


def source_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        marker = ROOT / "HERITAGE_SOURCE_COMMIT.txt"
        if not marker.exists():
            raise RuntimeError("Use the CROWN checkout or the prepared Heritage source bundle.")
        sha = marker.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("The local source identity is invalid.")
    return sha


def local_environment() -> dict[str, str]:
    # Inherit tool/network configuration, never application/provider credentials.
    prefixes = ("DJANGO_", "CROWN_", "VITE_", "AZURE_", "WEBSITE_", "TWILIO_", "MSAL_", "AAD_", "CELERY_", "SENTRY_", "STRIPE_", "PAYMENT_", "SENDGRID_", "MS_GRAPH_", "COMPUWERX_")
    excluded = {"DATABASE_URL", "SECRET_KEY", "DEBUG", "ENVIRONMENT", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS", "EMAIL_HOST_PASSWORD", "OPS_SECRET", "DEV_OPS_SECRET"}
    env = {key: value for key, value in os.environ.items() if key not in excluded and not key.startswith(prefixes)}
    STATE.mkdir(parents=True, exist_ok=True)
    secret_path = STATE / "django.key"
    if not secret_path.exists():
        secret_path.write_text(secrets.token_urlsafe(64), encoding="utf-8")
        secret_path.chmod(0o600)
    sha = source_sha()
    env.update({
        "DJANGO_DEBUG": "true", "DJANGO_ENV": "local", "CROWN_ENV": "local",
        "DJANGO_SECRET_KEY": secret_path.read_text(encoding="utf-8").strip(),
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
        "DATABASE_URL": "sqlite:///" + (STATE / "heritage.sqlite3").as_posix(),
        "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "true", "CROWN_DEMO_MODE": "false",
        "CROWN_DEV_OPEN_API": "false", "TENANT_HEADER_REQUIRED": "true",
        "BUILD_SHA": sha, "VITE_BUILD_SHA": sha, "GITHUB_SHA": sha,
        "VITE_API_BASE": "http://127.0.0.1:8000",
        "VITE_API_BASE_URL": "", "VITE_LOCAL_DEMO": "1",
        "VITE_AAD_CLIENT_ID": "", "VITE_AAD_TENANT_ID": "",
        "VITE_SANDBOX_MODE": "1", "VITE_DEMO_MODE": "sandbox", "VITE_ADMISSIONS_DEMO_PREFILL": "1",
        "CROWN_DEPLOY_TAG": "heritage-local", "PYTHONUNBUFFERED": "1",
        "NO_PROXY": "localhost,127.0.0.1", "no_proxy": "localhost,127.0.0.1",
    })
    return env


def npm_command() -> list[str]:
    node = shutil.which("node")
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not node or not npm:
        raise RuntimeError("Install Node.js 22.12+ (or 24+) with npm, then start again.")
    version = subprocess.check_output([node, "--version"], text=True).strip().lstrip("v")
    major, minor = map(int, version.split(".")[:2])
    if major < 22 or (major == 22 and minor < 12):
        raise RuntimeError("Node.js 22.12+ (or 24+) is required.")
    npm_path = Path(npm).resolve()
    if npm_path.suffix == ".js":
        return [node, str(npm_path)]
    cli = npm_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
    if cli.exists():
        return [node, str(cli)]
    if os.name != "nt":
        return [str(npm_path)]
    raise RuntimeError("npm's installation is incomplete. Reinstall Node.js with npm.")


def run(command: list[str], env: dict[str, str], cwd: Path = ROOT) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def preview_command() -> list[str]:
    # Launch Vite directly so shutdown stops the server, rather than only npm.
    return [shutil.which("node"), str(FRONTEND / "node_modules/vite/bin/vite.js"), "preview", "--host", "127.0.0.1", "--port", "4173", "--strictPort"]


def available_ports() -> None:
    for port in (8000, 4173):
        with socket.socket() as probe:
            # A stopped server can leave TCP connections in TIME_WAIT. Reuse
            # those addresses while still refusing a currently bound service.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(f"Port {port} is already in use. Close the earlier demo first.") from exc


def wait_ready(url: str, process: subprocess.Popen, timeout: int = 90) -> None:
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server stopped before {url} was ready. Read the demo logs.")
        try:
            with opener.open(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}. Read the demo logs.")


def prepare(env: dict[str, str], npm: list[str], skip_install: bool) -> Path:
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    create_venv = not python.exists()
    if create_venv:
        venv.create(ROOT / ".venv", with_pip=True)
    requirements = ROOT / "backend" / "requirements.txt"
    lock = FRONTEND / "package-lock.json"
    digest = hashlib.sha256(requirements.read_bytes() + lock.read_bytes()).hexdigest()
    marker = STATE / "dependencies.sha256"
    if not skip_install and (create_venv or not marker.exists() or marker.read_text() != digest or not (FRONTEND / "node_modules").exists()):
        print("Installing application dependencies (first start requires internet).", flush=True)
        run([str(python), "-m", "pip", "install", "-r", str(requirements)], env)
        run(npm + ["ci"], env, FRONTEND)
        marker.write_text(digest, encoding="utf-8")
    manage = [str(python), str(ROOT / "backend" / "manage.py")]
    run(manage + ["check"], env)
    run(manage + ["migrate", "--noinput"], env)
    initialized = STATE / "seed.complete"
    if not initialized.exists():
        print("Preparing fictional Heritage records in the isolated local database.", flush=True)
        run(manage + ["sandbox_seed_flagship"], env)
        run(manage + ["sandbox_proof_gate", "--strict"], env)
        initialized.write_text(env["BUILD_SHA"], encoding="utf-8")
    else:
        run(manage + ["sandbox_proof_gate", "--strict"], env)
    relationships = STATE / "relationships.complete"
    if not relationships.exists():
        run(manage + ["shell", "--command", "from sandbox_demo.services import seed_local_heritage_relationships; seed_local_heritage_relationships()"], env)
        relationships.write_text(env["BUILD_SHA"], encoding="utf-8")
    run(npm + ["run", "build"], env, FRONTEND)
    return python


def stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--skip-install", action="store_true", help="Use already-installed dependencies.")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 1
    processes: list[subprocess.Popen] = []
    logs = []
    try:
        available_ports()
        env = local_environment()
        npm = npm_command()
        python = prepare(env, npm, args.skip_install)
        if args.prepare_only:
            print("Heritage is prepared. Start again to open the demo.")
            return 0
        for name, command, cwd in [
            ("backend", [str(python), str(ROOT / "backend/manage.py"), "runserver", "127.0.0.1:8000", "--noreload"], ROOT),
            ("frontend", preview_command(), FRONTEND),
        ]:
            log = (STATE / f"{name}.log").open("w", encoding="utf-8")
            logs.append(log)
            processes.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT))
        wait_ready("http://127.0.0.1:8000/api/v1/sandbox/catalog/", processes[0])
        wait_ready(URL, processes[1])
        print(f"\nHeritage demo ready: {URL}\nChoose a role; no password is required.\nFictional data only. External payments are disabled.\nKeep this window open. Press Ctrl+C to stop.\nLogs: {STATE}", flush=True)
        if not args.no_browser:
            webbrowser.open(URL)
        while all(process.poll() is None for process in processes):
            time.sleep(1)
        raise RuntimeError("A demo server stopped. Read the demo logs.")
    except KeyboardInterrupt:
        print("\nHeritage demo stopped. Saved records remain available for the next session.")
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Heritage could not start: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)
        for log in logs:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
