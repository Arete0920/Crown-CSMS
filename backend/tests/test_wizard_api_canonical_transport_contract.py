import re
from pathlib import Path


WIZARD_CLIENTS = (
    "attendance_rules_wizard.js",
    "attendance_codes_wizard.js",
    "bell_schedule_wizard.js",
    "enrollment_conversion_wizard.js",
)


def test_target_wizard_clients_use_canonical_authenticated_transport():
    api_dir = Path(__file__).resolve().parents[2] / "frontend" / "dashboards" / "src" / "api"

    for filename in WIZARD_CLIENTS:
        source = (api_dir / filename).read_text(encoding="utf-8")
        assert re.search(
            r'import\s*\{[^}]*\bauthenticatedFetch\b[^}]*\}\s*from\s*["\']\.\./utils/authClient["\']',
            source,
        )
        assert "return authenticatedFetch(url, { ...init, validateStatus: () => true });" in source
        assert "return checkResponse(res, url);" in source or "return checkResponse(res, SESSIONS);" in source
        assert "globalThis.fetch(" not in source
        assert "window.fetch(" not in source
        assert not re.search(r"(?<![\w.])fetch\(", source)
        assert "getToken" not in source
        assert "Authorization: `Bearer" not in source


def test_canonical_transport_preserves_session_and_optional_bearer_behavior():
    auth_client = (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "dashboards"
        / "src"
        / "utils"
        / "authClient.js"
    ).read_text(encoding="utf-8")

    assert 'credentials: trustedApiRequest ? (requestInit.credentials ?? "include")' in auth_client
    assert 'if (token && !headers.has("Authorization"))' in auth_client
    assert 'headers.set("Authorization", `Bearer ${token}`)' in auth_client
    assert 'if (schoolId && !headers.has("X-School-Id"))' in auth_client
    assert 'if (!headers.has("X-Correlation-Id"))' in auth_client
