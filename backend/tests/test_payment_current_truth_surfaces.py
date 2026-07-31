from pathlib import Path
import uuid

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8-sig")


def test_payment_provider_normalizer_is_fail_closed() -> None:
    from platform_ops.provisioning import (
        PAYMENT_PROCESSING_DISABLED_MESSAGE,
        normalize_payment_provider,
    )

    assert normalize_payment_provider(None) == "none"
    assert normalize_payment_provider(" NONE ") == "none"
    assert normalize_payment_provider("manual") == "manual"

    for provider in ("stripe", "paypal", "square", "adyen", ""):
        if provider == "":
            assert normalize_payment_provider(provider) == "none"
            continue
        with pytest.raises(ValueError, match="External payment processing is disabled") as exc:
            normalize_payment_provider(provider)
        assert str(exc.value) == PAYMENT_PROCESSING_DISABLED_MESSAGE


@pytest.mark.django_db(transaction=True)
def test_provisioning_rejects_external_provider_without_writes() -> None:
    from platform_ops.models import ProvisioningJob
    from platform_ops.provisioning import create_school_and_queue_provisioning
    from tenants.models import TenantProfile

    with pytest.raises(ValueError, match="External payment processing is disabled"):
        create_school_and_queue_provisioning(
            name="Rejected Provider School",
            slug=f"rejected-provider-{uuid.uuid4().hex[:8]}",
            payment_provider="stripe",
            idempotency_key=str(uuid.uuid4()),
        )

    assert ProvisioningJob.objects.count() == 0
    assert TenantProfile.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_provisioning_accepts_manual_payment_mode() -> None:
    from platform_ops.provisioning import create_school_and_queue_provisioning
    from tenants.models import TenantProfile

    job = create_school_and_queue_provisioning(
        name="Manual Payment School",
        slug=f"manual-payment-{uuid.uuid4().hex[:8]}",
        payment_provider="manual",
        idempotency_key=str(uuid.uuid4()),
    )

    profile = TenantProfile.objects.get(school_id=job.school_id)
    assert profile.payment_provider == "manual"


def test_current_tenant_state_has_no_external_provider_choice() -> None:
    tenant_models = _read("backend/tenants/models.py")
    migration = _read("backend/tenants/migrations/0002_alter_tenantprofile_payment_provider.py")

    assert '("stripe", "Stripe Connect")' not in tenant_models
    assert '("manual", "Manual / Invoice")' in tenant_models
    assert '("none", "None / Disabled")' in tenant_models
    assert '("manual", "Manual / Invoice")' in migration
    assert '("none", "None / Disabled")' in migration


def test_frontend_payment_authority_is_fail_closed() -> None:
    authority = _read(
        "frontend/dashboards/src/modules/advancement/paymentAvailability.js"
    )

    assert "PAYMENT_PROCESSING_ENABLED = false" in authority
    assert "Online payment processing is not enabled" in authority
