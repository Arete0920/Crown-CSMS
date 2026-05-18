"""
Solomon Context Adapter Base Class

Defines the contract for safe, fail-closed internal context consumption.
Adapters query SOLOMON read-only and return deterministic payloads.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from django.http import HttpRequest


@dataclass
class SolomonContextRequest:
    """Request contract for SOLOMON context lookup."""

    module: str  # e.g., "onboarding", "finance", "academics", "spiritual_life"
    route: str  # e.g., "/students/enrollment"
    audience: Optional[str] = None  # e.g., "parent", "student", "staff"
    scope: Optional[str] = None  # e.g., "school", "global"
    request: Optional[HttpRequest] = None  # Current request for tenant context


@dataclass
class SolomonContextPayload:
    """Response contract for SOLOMON context."""

    status: str  # "resolved", "empty", "disabled", "error"
    resources: List[Dict[str, Any]] = field(default_factory=list)
    playbooks: List[Dict[str, Any]] = field(default_factory=list)
    context_rules: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "resources": self.resources,
            "playbooks": self.playbooks,
            "context_rules": self.context_rules,
            "metadata": self.metadata,
        }


class BaseSolomonAdapter(ABC):
    """
    Base adapter for internal SOLOMON context consumption.

    Enforces fail-closed semantics:
    - Returns empty payload when context layer is disabled
    - Returns empty payload when no matching context found
    - Never raises exceptions; always returns valid SolomonContextPayload
    """

    def __init__(self):
        """Initialize adapter with context resolution services."""
        from solomon.services import (
            SolomonContextResolver,
            visible_resources,
            visible_playbooks,
            visible_context_rules,
        )

        self.resolver = SolomonContextResolver
        self.visible_resources = visible_resources
        self.visible_playbooks = visible_playbooks
        self.visible_context_rules = visible_context_rules

    def get_context(self, req: SolomonContextRequest) -> SolomonContextPayload:
        """
        Main entry point for context retrieval.

        Args:
            req: SolomonContextRequest with module, route, audience, scope

        Returns:
            SolomonContextPayload (never raises; always returns valid payload)
        """
        from django.conf import settings

        # Fail-closed: disabled flag returns empty payload
        if not getattr(settings, "CROWN_SOLOMON_CONTEXT_ENABLED", False):
            return SolomonContextPayload(status="disabled")

        try:
            return self._resolve_context(req)
        except Exception as e:
            # Fail-closed: any exception returns error payload, does not bubble
            return SolomonContextPayload(
                status="error",
                metadata={"error_type": type(e).__name__, "error_msg": str(e)},
            )

    @abstractmethod
    def _resolve_context(
        self, req: SolomonContextRequest
    ) -> SolomonContextPayload:
        """
        Subclass must implement context resolution logic.

        Should query SOLOMON read-only and return deterministic payload.

        Args:
            req: SolomonContextRequest

        Returns:
            SolomonContextPayload
        """
        pass

    def _empty_payload(self) -> SolomonContextPayload:
        """Return empty payload (no context found, but not an error)."""
        return SolomonContextPayload(status="empty")

    def _resolved_payload(
        self,
        resources: List[Dict[str, Any]] = None,
        playbooks: List[Dict[str, Any]] = None,
        context_rules: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None,
    ) -> SolomonContextPayload:
        """Return resolved payload with context items."""
        return SolomonContextPayload(
            status="resolved",
            resources=resources or [],
            playbooks=playbooks or [],
            context_rules=context_rules or [],
            metadata=metadata or {},
        )
