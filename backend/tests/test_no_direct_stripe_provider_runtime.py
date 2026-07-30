from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DIRECT_PROVIDER_RUNTIME_FILES = {
    "backend/requirements.txt",
    "backend/payments/providers/__init__.py",
    "backend/advancement/payments/providers.py",
    "backend/advancement/payments/service.py",
}
REMOVED_RUNTIME_PATHS = {
    "backend/payments/providers/stripe_connect.py",
    "backend/advancement/stripe_helpers.py",
}
FORBIDDEN_DIRECT_PROVIDER_TOKENS = {
    "stripeconnect",
    "stripeprovider",
    "import stripe",
    "stripe>=",
    "stripe==",
}


def _read(relative_path: str) -> str:
    path = REPOSITORY_ROOT / relative_path
    assert path.is_file(), f"Missing expected repository file: {relative_path}"
    return path.read_text(encoding="utf-8")


def test_direct_stripe_provider_runtime_is_absent() -> None:
    for relative_path in sorted(REMOVED_RUNTIME_PATHS):
        assert not (REPOSITORY_ROOT / relative_path).exists(), (
            f"Removed provider-specific runtime path still exists: {relative_path}"
        )

    violations: list[str] = []
    for relative_path in sorted(DIRECT_PROVIDER_RUNTIME_FILES):
        content = _read(relative_path).lower()
        for token in sorted(FORBIDDEN_DIRECT_PROVIDER_TOKENS):
            if token in content:
                violations.append(f"{relative_path}: {token}")

    assert violations == [], f"Direct Stripe provider runtime remains: {violations}"


def test_provider_registry_remains_explicitly_in_process_only() -> None:
    service = _read("backend/advancement/payments/service.py")
    provider_package = _read("backend/payments/providers/__init__.py")

    assert '"fake": FakeProvider' in service
    assert "return FakeProvider()" in service
    assert "return FakeCheckoutProvider()" in service
    assert '__all__ = ["DeferredPaymentGateway", "get_gateway"]' in provider_package


def test_provider_specific_settings_and_webhook_execution_are_absent() -> None:
    settings = _read("backend/crown_api/settings.py")
    advancement_api = _read("backend/advancement/api.py")

    assert "No external payment provider is selected or authorized." in settings
    for forbidden in (
        "ADVANCEMENT_PAYMENT_PROVIDER",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ):
        assert forbidden not in settings

    for forbidden in (
        "def stripe_webhook",
        "HTTP_STRIPE_SIGNATURE",
        "STRIPE_WEBHOOK_SECRET",
        "_create_receipt_and_queue_email",
        "get_checkout_provider",
    ):
        assert forbidden not in advancement_api


def test_provider_neutral_line_item_helper_replaces_stripe_named_module() -> None:
    helper = _read("backend/advancement/payment_line_items.py")
    stage_tests = _read("backend/advancement/tests/test_advancement_stage3_4.py")
    services = _read("backend/advancement/services_stage3_2.py")
    models = _read("backend/advancement/models_stage3_2.py")

    assert "compute_totals_from_line_items" in helper
    assert "from advancement.payment_line_items import" in stage_tests
    assert "Stripe" not in helper
    assert "Stripe" not in services
    assert "Stripe" not in models


def test_legacy_provider_webhook_route_remains_an_explicit_404_tombstone() -> None:
    urls = _read("backend/advancement/urls.py")
    hold_views = _read("backend/advancement/payment_hold_views.py")

    assert 'path("payments/stripe/webhook/", provider_webhook_not_configured' in urls
    assert "def provider_webhook_not_configured" in hold_views
    assert "return HttpResponseNotFound()" in hold_views
    assert "stripe_webhook" not in hold_views


def test_removed_webhook_is_not_an_approved_csrf_exception() -> None:
    policy_markdown = _read("docs/security/CSRF_EXCEPTION_POLICY_MATRIX.md")
    policy_json = _read("docs/security/csrf_exception_policy_matrix.json")

    assert "stripe_webhook" not in policy_markdown
    assert "stripe_webhook" not in policy_json
