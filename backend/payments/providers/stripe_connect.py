"""
Stripe Connect payment orchestration.

Provides StripeConnect — a thin wrapper around the Stripe SDK for
creating and managing connected accounts for school tenants.

IMPORTANT: The `stripe` package is a soft dependency.
  - Install: pip install stripe
  - Configure: set STRIPE_SECRET_KEY env var (and STRIPE_WEBHOOK_SECRET for webhooks)
  - Never log or expose the secret key.

This class is intentionally minimal (MVP).  It does not handle webhooks,
refunds, disputes, or subscription management.  Those are Phase 2.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


def _get_stripe():
    """Import stripe lazily so the app doesn't crash if the package isn't installed."""
    try:
        import stripe  # noqa: PLC0415
        return stripe
    except ImportError as exc:
        raise RuntimeError(
            "The 'stripe' package is required for Stripe Connect. "
            "Install it with: pip install stripe"
        ) from exc


class StripeConnect:
    """
    Stripe Connect orchestration for Crown2026 school tenants.

    Each school tenant gets its own Stripe Connected Account so that
    tuition/billing payments are processed under their identity and
    Crown2026 takes a platform fee.

    Usage:
        provider = StripeConnect()
        account_id = provider.create_connected_account(school_id, email)
        link = provider.onboarding_link(account_id, return_url, refresh_url)
    """

    def __init__(self, secret_key: Optional[str] = None) -> None:
        self._secret_key = secret_key or os.getenv("STRIPE_SECRET_KEY", "")
        if not self._secret_key:
            logger.warning(
                "StripeConnect: STRIPE_SECRET_KEY is not set. "
                "All calls will fail until a key is configured."
            )

    def _stripe(self):
        stripe = _get_stripe()
        stripe.api_key = self._secret_key
        return stripe

    def create_connected_account(
        self,
        school_id: uuid.UUID,
        email: str,
    ) -> str:
        """
        Create a Stripe Express connected account for a school tenant.

        Returns the Stripe account ID string (e.g. "acct_xxxxxxxxxx").
        The account ID should be stored in TenantProfile.stripe_account_id.

        Args:
            school_id: Crown2026 school UUID (stored in metadata for correlation).
            email:     Contact email for the school's Stripe account.
        """
        stripe = self._stripe()
        account = stripe.Account.create(
            type="express",
            email=email,
            metadata={"crown_school_id": str(school_id)},
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        logger.info(
            "StripeConnect.create_connected_account: school=%s account=%s",
            school_id,
            account.id,
        )
        return account.id

    def onboarding_link(
        self,
        account_id: str,
        return_url: str,
        refresh_url: str,
    ) -> str:
        """
        Generate a one-time Stripe Connect onboarding link.

        The returned URL should be presented to the school administrator.
        It expires after Stripe's standard timeout (~5 minutes).

        Args:
            account_id:  Stripe account ID from create_connected_account().
            return_url:  URL Stripe redirects to after successful onboarding.
            refresh_url: URL Stripe redirects to if the link expires.
        """
        stripe = self._stripe()
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
        )
        logger.info(
            "StripeConnect.onboarding_link: account=%s url=<hidden>",
            account_id,
        )
        return link.url

    def retrieve_account(self, account_id: str) -> dict:
        """
        Retrieve current state of a connected account.

        Returns a dict with keys: id, charges_enabled, payouts_enabled, details_submitted.
        """
        stripe = self._stripe()
        account = stripe.Account.retrieve(account_id)
        return {
            "id": account.id,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "details_submitted": account.details_submitted,
        }
