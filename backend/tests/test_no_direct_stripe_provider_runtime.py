from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = {
    "backend/requirements.txt",
    "backend/payments/providers/__init__.py",
    "backend/advancement/payments/providers.py",
    "backend/advancement/payments/service.py",
}
REMOVED_PROVIDER = "backend/payments/providers/stripe_connect.py"
FORBIDDEN_RUNTIME_TOKENS = {
    "stripeconnect",
    "stripeprovider",
    "import stripe",
    "stripe>=",
    "stripe==",
}


def test_direct_stripe_provider_runtime_is_absent() -> None:
    removed_path = REPOSITORY_ROOT / REMOVED_PROVIDER
    assert not removed_path.exists(), f"Direct provider wrapper still exists: {REMOVED_PROVIDER}"

    violations: list[str] = []
    for relative_path in sorted(RUNTIME_FILES):
        path = REPOSITORY_ROOT / relative_path
        assert path.is_file(), f"Missing expected runtime file: {relative_path}"
        content = path.read_text(encoding="utf-8").lower()
        for token in sorted(FORBIDDEN_RUNTIME_TOKENS):
            if token in content:
                violations.append(f"{relative_path}: {token}")

    assert violations == [], f"Direct Stripe provider runtime remains: {violations}"


def test_provider_registry_remains_explicitly_in_process_only() -> None:
    service = (
        REPOSITORY_ROOT / "backend/advancement/payments/service.py"
    ).read_text(encoding="utf-8")
    provider_package = (
        REPOSITORY_ROOT / "backend/payments/providers/__init__.py"
    ).read_text(encoding="utf-8")

    assert '"fake": FakeProvider' in service
    assert "return FakeProvider()" in service
    assert "return FakeCheckoutProvider()" in service
    assert '__all__ = ["DeferredPaymentGateway", "get_gateway"]' in provider_package
