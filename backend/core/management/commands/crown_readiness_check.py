from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Run Crown production readiness probes."

    def handle(self, *args, **options):
        failures = []

        if settings.DEBUG:
            failures.append("DEBUG must be False in production.")

        if not settings.SECRET_KEY:
            failures.append("SECRET_KEY missing.")

        allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
        if not allowed_hosts or "*" in allowed_hosts:
            failures.append("ALLOWED_HOSTS must be explicit.")

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:
            failures.append(f"Database probe failed: {exc}")

        try:
            cache.set("crown_readiness_probe", "ok", timeout=30)
            if cache.get("crown_readiness_probe") != "ok":
                failures.append("Cache probe failed.")
        except Exception as exc:
            failures.append(f"Cache probe failed: {exc}")

        if failures:
            for failure in failures:
                self.stderr.write(self.style.ERROR(failure))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("CROWN_PRODUCTION_READINESS_PASS"))
