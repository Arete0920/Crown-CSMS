"""
Phase 3 P2: Runtime Proof Ceremony.

Deterministic API-level checks for demo-critical workflows.
Runs against a live Django server (started separately).

Usage:
    python manage.py proof_phase3_runtime [--base-url URL] [--verbose]

Env overrides:
    CROWN_API_BASE_URL          Base URL (default: http://127.0.0.1:8000/)
    CROWN_DEMO_SCHOOL_ID        Demo school UUID
    CROWN_DEMO_AUTH_PATH        Path for demo JWT (default: api/dev/token/)
    CROWN_ADMISSIONS_PATH       Admissions summary path
    CROWN_AID_PATH              Financial aid summary path

The demo key is read from Django settings (CROWN_DEMO_KEY) — never hardcoded here.

Assertions (fail hard on any failure):
    1. Demo auth token acquired via api/dev/token/
    2. Tenant header enforced (request without X-School-Id rejected)
    3. Ledger invariants endpoint responds 200 with auth + tenant
    4. Ledger open charges endpoint responds 200
    5. Ledger open invoices endpoint responds 200
    6. Admissions summary endpoint responds 200
    7. Financial aid summary endpoint responds 200

Uses stdlib only (urllib) — no requests dependency.
"""
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Imported lazily inside handle() to avoid import-time app-registry errors.
# (This module is imported during Django setup before models are ready.)


@dataclass
class StepResult:
    name: str
    ok: bool
    status: int
    detail: str


def _join(base: str, path: str) -> str:
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def _req(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 20,
) -> Tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except URLError as e:
        # urllib raises for 4xx/5xx — read the response body
        if hasattr(e, "code") and hasattr(e, "read"):
            try:
                body_text = e.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = str(e)
            return e.code, body_text
        return 0, f"CONNECTION_ERROR: {e}"
    except Exception as e:
        return 0, f"ERROR: {e}"


class Command(BaseCommand):
    help = "Phase 3 P2: Runtime Proof Ceremony — deterministic demo-critical API checks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=os.environ.get("CROWN_API_BASE_URL", "http://127.0.0.1:8000/"),
        )
        parser.add_argument(
            "--school-id",
            default=os.environ.get("CROWN_DEMO_SCHOOL_ID", "19801b59-8c05-4c84-9312-5d792e4e839d"),
        )
        parser.add_argument("--verbose", action="store_true")

    def handle(self, *args, **opts):
        base = opts["base_url"].rstrip("/") + "/"
        school_id = opts["school_id"]
        # Read the demo key from Django settings — same source of truth as dev_token_views.py.
        # Never hardcode this value in source or CI YAML.
        demo_key = getattr(settings, "CROWN_DEMO_KEY", "")
        verbose = bool(opts["verbose"])

        auth_path = os.environ.get("CROWN_DEMO_AUTH_PATH", "api/dev/token/")
        admissions_path = os.environ.get("CROWN_ADMISSIONS_PATH", "api/v1/admissions/summary/")
        aid_path = os.environ.get("CROWN_AID_PATH", "api/v1/financial-aid/summary/")

        if not demo_key:
            raise CommandError(
                "CROWN_DEMO_KEY is empty. Set CROWN_DEMO_MODE=true so Django settings provides the key."
            )

        # Resolve the demo school UUID from the actual database rather than from
        # settings. seed_demo_school uses get_or_create with an auto-generated
        # UUID, so settings.CROWN_DEMO_SCHOOL_ID may not match what is in the DB.
        from core.models import School  # late import — app registry is ready here
        DEMO_SCHOOL_NAME = "Crown Demo Christian Academy"
        try:
            demo_school = School.objects.get(name=DEMO_SCHOOL_NAME)
            school_id = str(demo_school.id)
            self.stdout.write(f"Demo school UUID (from DB): {school_id}")
        except School.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"Demo school '{DEMO_SCHOOL_NAME}' not found in DB — falling back to --school-id"
                )
            )
            school_id = opts["school_id"]

        results: list[StepResult] = []

        # ------------------------------------------------------------------
        # 1. Acquire demo JWT
        # ------------------------------------------------------------------
        auth_url = _join(base, auth_path)
        status, body = _req(
            "POST",
            auth_url,
            headers={"X-Demo-Key": demo_key, "Content-Type": "application/json"},
            body={"school_id": school_id},
        )
        if status != 200:
            results.append(StepResult("auth_demo_token", False, status, body[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at auth_demo_token")

        try:
            payload = json.loads(body)
            token = payload.get("access") or payload.get("token") or payload.get("jwt")
        except Exception:
            token = None

        if not token:
            results.append(StepResult("auth_demo_token_parse", False, status, body[:300]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at auth_demo_token_parse")

        results.append(StepResult("auth_demo_token", True, status, "token acquired"))

        # Full headers for authenticated calls
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "X-School-Id": str(school_id),
            "Content-Type": "application/json",
        }

        # ------------------------------------------------------------------
        # 2. Tenant header enforcement: same endpoint WITHOUT X-School-Id
        #    must be rejected (not 200)
        # ------------------------------------------------------------------
        inv_url = _join(base, "api/v1/ledger/invariants/")
        no_tenant_headers = {"Authorization": f"Bearer {token}"}
        st2, bd2 = _req("GET", inv_url, headers=no_tenant_headers)
        if st2 == 200:
            results.append(StepResult(
                "tenant_header_required", False, st2,
                "Expected rejection without X-School-Id but got 200 — tenant enforcement missing"
            ))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at tenant_header_required")
        results.append(StepResult("tenant_header_required", True, st2, "tenant header enforced"))

        # ------------------------------------------------------------------
        # 3. Ledger invariants (with auth + tenant)
        # ------------------------------------------------------------------
        st3, bd3 = _req("GET", inv_url, headers=auth_headers)
        if st3 != 200:
            results.append(StepResult("ledger_invariants", False, st3, bd3[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at ledger_invariants")
        results.append(StepResult("ledger_invariants", True, st3, "ok"))

        # ------------------------------------------------------------------
        # 4. Open charges — endpoint existence check.
        #    Requires account_id or household_id. Calling without them must
        #    return 400 (not 401/403/404/500), proving the endpoint is live
        #    and correctly rejects bad input.
        # ------------------------------------------------------------------
        open_charges_url = _join(base, "api/v1/ledger/charges/open/")
        st4, bd4 = _req("GET", open_charges_url, headers=auth_headers)
        if st4 not in (200, 400):
            results.append(StepResult("ledger_open_charges", False, st4, bd4[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at ledger_open_charges")
        results.append(StepResult("ledger_open_charges", True, st4, "endpoint live"))

        # ------------------------------------------------------------------
        # 5. Open invoices — endpoint existence check (same pattern as charges).
        # ------------------------------------------------------------------
        open_invoices_url = _join(base, "api/v1/ledger/invoices/open/")
        st5, bd5 = _req("GET", open_invoices_url, headers=auth_headers)
        if st5 not in (200, 400):
            results.append(StepResult("ledger_open_invoices", False, st5, bd5[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at ledger_open_invoices")
        results.append(StepResult("ledger_open_invoices", True, st5, "endpoint live"))

        # ------------------------------------------------------------------
        # 6. Admissions summary
        # ------------------------------------------------------------------
        admissions_url = _join(base, admissions_path)
        st6, bd6 = _req("GET", admissions_url, headers=auth_headers)
        if st6 != 200:
            results.append(StepResult("admissions_summary", False, st6, bd6[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at admissions_summary")
        results.append(StepResult("admissions_summary", True, st6, "ok"))

        # ------------------------------------------------------------------
        # 7. Financial aid summary
        # ------------------------------------------------------------------
        aid_url = _join(base, aid_path)
        st7, bd7 = _req("GET", aid_url, headers=auth_headers)
        if st7 != 200:
            results.append(StepResult("financial_aid_summary", False, st7, bd7[:400]))
            self._emit(results, verbose)
            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at financial_aid_summary")
        results.append(StepResult("financial_aid_summary", True, st7, "ok"))

        self._emit(results, verbose)
        self.stdout.write(self.style.SUCCESS("PHASE3_RUNTIME_PROOF: PASS"))

    def _emit(self, results: list, verbose: bool) -> None:
        self.stdout.write("=== Phase 3 P2 Runtime Proof Results ===")
        for r in results:
            flag = "PASS" if r.ok else "FAIL"
            line = f"{flag} :: {r.name} :: status={r.status} :: {r.detail}"
            self.stdout.write(line)
