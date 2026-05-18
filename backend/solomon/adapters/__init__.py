"""
Solomon Internal Context Adapters

Provide fail-closed, deterministic context resolution for CROWN modules.
Each adapter queries SOLOMON read-only and returns safe payloads.
"""

from solomon.adapters.base import (
    BaseSolomonAdapter,
    SolomonContextRequest,
    SolomonContextPayload,
)
from solomon.adapters.onboarding_adapter import OnboardingAdapter
from solomon.adapters.finance_adapter import FinanceAdapter
from solomon.adapters.academics_adapter import AcademicsAdapter
from solomon.adapters.spiritual_life_adapter import SpiritualLifeAdapter

__all__ = [
    "BaseSolomonAdapter",
    "SolomonContextRequest",
    "SolomonContextPayload",
    "OnboardingAdapter",
    "FinanceAdapter",
    "AcademicsAdapter",
    "SpiritualLifeAdapter",
]
