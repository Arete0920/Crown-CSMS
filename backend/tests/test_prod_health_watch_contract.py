"""Regression coverage for the manual production health alert control."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PARSER = REPO_ROOT / "tools/ci/prod_health_status.py"
WORKFLOW = REPO_ROOT / ".github/workflows/prod-health-watch.yml"

spec = importlib.util.spec_from_file_location("prod_health_status", PARSER)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_actual_crown_api_health_contract_is_healthy():
    assert module.classify_health({"ok": True, "status": "ok", "build_sha": "a" * 40}) == "healthy"


def test_legacy_supported_health_contract():
    assert module.classify_health({"status": "healthy"}) == "healthy"
    assert module.classify_health({"ok": True}) == "healthy"


def test_degraded_is_not_reported_as_healthy_even_if_ok_flag_is_true():
    assert module.classify_health({"ok": True, "status": "degraded"}) == "degraded"


def test_conflicting_health_flags_fail_closed():
    assert module.classify_health({"status": "healthy", "ok": False}) == "unhealthy"
    assert module.classify_health({"status": "ok", "ok": "false"}) == "unhealthy"
    assert module.classify_health({"status": "error", "ok": True}) == "unhealthy"


def test_unexpected_or_injectable_payload_is_never_echoed_as_status():
    for value in ["' + process.exit(1) + '", "$(touch /tmp/unsafe)", "healthy\\ninjected=true", ["healthy"], 42]:
        result = module.classify_health({"status": value, "ok": False})
        assert result in {"healthy", "degraded", "unhealthy"}
        assert result == "unhealthy"


def test_non_json_and_non_object_fail_closed(tmp_path):
    for bad in ["not json", "[]", "null", '{"status":"ok","ok":false}']:
        file = tmp_path / "response.json"
        file.write_text(bad, encoding="utf-8")
        completed = subprocess.run([sys.executable, str(PARSER), str(file)], check=True, capture_output=True, text=True)
        assert completed.stdout.strip() == "unhealthy"


def test_missing_health_response_fails_closed(tmp_path):
    completed = subprocess.run([sys.executable, str(PARSER), str(tmp_path / "absent.json")], check=True, capture_output=True, text=True)
    assert completed.stdout.strip() == "unhealthy"


def test_manual_only_dispatch_and_fail_closed_alerting():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "  workflow_dispatch:" in text
    assert "\n  schedule:" not in text
    assert "if: always() && steps.health.outputs.status != 'healthy'" in text
    assert "Report any failed production health status" in text
    assert "Fail closed when health proof is not healthy" in text


def test_untrusted_health_output_is_never_interpolated_into_scripts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "const status = process.env.HEALTH_STATUS || 'unknown';" in text
    assert "const httpCode = process.env.HEALTH_HTTP_CODE || '000';" in text
    assert "const status = '${{ steps.health.outputs.status }}'" not in text
    assert "const httpCode = '${{ steps.health.outputs.http_code }}'" not in text
    assert 'echo "Production health proof failed: status=${{ steps.health.outputs.status }}' not in text


def test_workflow_has_no_secret_logs():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'echo "${PRODUCTION_URL}"' not in text
    assert "PRODUCTION_URL: ${{ secrets.PRODUCTION_URL }}" in text


def test_pinned_checkout_precedes_local_parser_execution():
    text = WORKFLOW.read_text(encoding="utf-8")
    checkout = "uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11"
    health = "- name: Check production health endpoint"
    parser = "python3 tools/ci/prod_health_status.py /tmp/health_response.json"
    assert checkout in text
    assert text.index(checkout) < text.index(health) < text.index(parser)
    assert "persist-credentials: false" in text[text.index(checkout):text.index(health)]
