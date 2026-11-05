"""Exercise application counters using two workers and a disposable Redis.

No target URL is accepted. Redis listens only on a private temporary Unix socket;
the harness never loads application deployment settings or contacts hosted Redis.
"""

import hashlib
import importlib.util
import multiprocessing
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUTH_SOURCE = ROOT / "backend/crown_api/auth_rate_limit.py"


def _worker(connection, socket_path, barrier):
    try:
        from django.conf import settings
        from redis.backoff import NoBackoff
        from redis.retry import Retry

        settings.configure(
            CROWN_AUTH_RATE_LIMIT_REQUIRE_SHARED_CACHE=True,
            CACHES={"default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "unix://" + socket_path,
                "OPTIONS": {
                    "socket_timeout": 1,
                    "socket_connect_timeout": 1,
                    "retry": Retry(NoBackoff(), 0),
                },
            }},
        )
        # Import the actual counter file without executing crown_api/__init__,
        # which also boots Celery and application-wide schema extensions.
        spec = importlib.util.spec_from_file_location("isolated_auth_counters", AUTH_SOURCE)
        counters = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = counters
        spec.loader.exec_module(counters)

        connection.send({"ready": True})
        while True:
            command = connection.recv()
            operation = command.pop("operation")
            if operation == "stop":
                return
            request = SimpleNamespace(
                META={"REMOTE_ADDR": command.pop("ip", "203.0.113.91")}
            )
            arguments = {
                "scope": command.pop("scope", "crown-login"),
                "identity": command.pop("identity", "synthetic@example.invalid"),
            }
            if operation == "check":
                result = counters.check_auth_rate_limit(request, **arguments, **command)
                connection.send({
                    "allowed": result.allowed,
                    "backend_available": result.backend_available,
                })
            elif operation == "record":
                try:
                    if command.pop("concurrent", False):
                        barrier.wait(timeout=5)
                    for _ in range(command.pop("count", 1)):
                        counters.record_auth_failure(request, **arguments, window_seconds=300)
                except counters.AuthRateLimitBackendUnavailable:
                    connection.send({"unavailable": True})
                else:
                    connection.send({"unavailable": False})
            elif operation == "clear":
                counters.clear_auth_identity_failures(request, **arguments)
                connection.send({"cleared": True})
            else:
                raise ValueError("Unknown synthetic worker operation")
    except Exception as exc:
        # Emit only the exception class, never connection details or payloads.
        connection.send({"worker_error": type(exc).__name__})
    finally:
        connection.close()


class Worker:
    def __init__(self, socket_path, barrier):
        context = multiprocessing.get_context("spawn")
        self.connection, child = context.Pipe()
        self.process = context.Process(target=_worker, args=(child, socket_path, barrier))
        self.process.start()
        child.close()

    def receive(self):
        if not self.connection.poll(10):
            raise AssertionError("Synthetic worker did not reply within 10 seconds")
        result = self.connection.recv()
        if "worker_error" in result:
            raise AssertionError("Synthetic worker failed: " + result["worker_error"])
        return result

    def send(self, operation, **arguments):
        self.connection.send({"operation": operation, **arguments})

    def call(self, operation, **arguments):
        self.send(operation, **arguments)
        return self.receive()

    def close(self):
        try:
            if self.process.is_alive():
                self.send("stop")
        except (OSError, EOFError):
            pass
        self.process.join(3)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(3)
        self.connection.close()
        self.process.close()


class RedisAcceptance(unittest.TestCase):
    def setUp(self):
        from redis import Redis
        from redis.backoff import NoBackoff
        from redis.exceptions import ConnectionError, TimeoutError
        from redis.retry import Retry

        binary = shutil.which("redis-server")
        self.assertIsNotNone(binary, "redis-server is required; verification cannot skip")
        # A short path avoids the platform's Unix-domain socket path limit.
        directory = tempfile.TemporaryDirectory(prefix="crown-auth-", dir="/tmp")
        self.addCleanup(directory.cleanup)
        socket_path = str(Path(directory.name) / "redis.sock")
        self.server = subprocess.Popen(
            [binary, "--port", "0", "--unixsocket", socket_path,
             "--unixsocketperm", "700", "--save", "", "--appendonly", "no",
             "--daemonize", "no", "--dir", directory.name],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self.stop_server)
        client = Redis(
            unix_socket_path=socket_path, socket_timeout=1,
            socket_connect_timeout=1, retry=Retry(NoBackoff(), 0),
        )
        self.addCleanup(client.close)
        deadline = time.monotonic() + 5
        while True:
            self.assertIsNone(self.server.poll(), "Disposable Redis exited during startup")
            try:
                if client.ping():
                    break
            except (ConnectionError, TimeoutError):
                pass
            if time.monotonic() >= deadline:
                self.fail("Disposable Redis did not become ready within 5 seconds")
            time.sleep(0.05)
        self.workers = []
        barrier = multiprocessing.get_context("spawn").Barrier(2)
        for _ in range(2):
            worker = Worker(socket_path, barrier)
            self.addCleanup(worker.close)
            self.assertEqual(worker.receive(), {"ready": True})
            self.workers.append(worker)

    def stop_server(self):
        if self.server.poll() is None:
            self.server.terminate()
            try:
                self.server.wait(3)
            except subprocess.TimeoutExpired:
                self.server.kill()
                self.server.wait(3)

    def test_each_auth_scope_shares_failure_threshold_between_workers(self):
        first, second = self.workers
        for scope, limit, ip_limit in (
            ("crown-login", 10, 50), ("simplejwt-login", 10, 50),
            ("crown-refresh", 10, 50), ("simplejwt-refresh", 20, 100),
        ):
            with self.subTest(scope=scope):
                arguments = dict(scope=scope, identity_limit=limit, ip_limit=ip_limit)
                self.assertEqual(first.call("check", **arguments),
                                 {"allowed": True, "backend_available": True})
                self.assertEqual(first.call("record", scope=scope, count=limit - 1),
                                 {"unavailable": False})
                self.assertTrue(second.call("check", **arguments)["allowed"])
                self.assertEqual(second.call("record", scope=scope), {"unavailable": False})
                for worker in self.workers:
                    self.assertEqual(worker.call("check", **arguments),
                                     {"allowed": False, "backend_available": True})

    def test_concurrent_increments_do_not_lose_failures(self):
        for worker in self.workers:
            worker.send("record", count=25, concurrent=True)
        for worker in self.workers:
            self.assertEqual(worker.receive(), {"unavailable": False})
        for worker in self.workers:
            self.assertFalse(worker.call("check", identity_limit=50, ip_limit=100)["allowed"])
            self.assertTrue(worker.call("check", identity_limit=51, ip_limit=100)["allowed"])

    def test_identity_cleanup_retains_ip_counter_and_other_buckets(self):
        first, second = self.workers
        self.assertEqual(first.call("record", count=10), {"unavailable": False})
        self.assertTrue(second.call("check", ip="203.0.113.92")["allowed"])
        self.assertTrue(second.call("check", scope="crown-refresh")["allowed"])
        self.assertEqual(second.call("clear"), {"cleared": True})
        self.assertTrue(first.call("check")["allowed"])
        self.assertEqual(first.call("check", identity="other@example.invalid", ip_limit=10),
                         {"allowed": False, "backend_available": True})

    def test_both_workers_fail_closed_after_owned_redis_stops(self):
        for worker in self.workers:
            self.assertTrue(worker.call("check")["allowed"])
        self.stop_server()
        for worker in self.workers:
            self.assertEqual(worker.call("check"),
                             {"allowed": False, "backend_available": False})
            self.assertEqual(worker.call("record"), {"unavailable": True})


if __name__ == "__main__":
    print("auth_rate_limit_sha256=" + hashlib.sha256(AUTH_SOURCE.read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
