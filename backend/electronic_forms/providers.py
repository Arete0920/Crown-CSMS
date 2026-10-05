from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SignatureProvider(Protocol):
    code: str

    def prepare_envelope(self, envelope) -> dict:
        ...

    def void_envelope(self, envelope) -> dict:
        ...


@dataclass(frozen=True)
class NativeSignatureProvider:
    """CROWN-owned provider. Performs no external network call."""

    code: str = "crown_native"

    def prepare_envelope(self, envelope) -> dict:
        return {
            "provider": self.code,
            "envelope_id": str(envelope.id),
            "external_reference": "",
        }

    def void_envelope(self, envelope) -> dict:
        return {
            "provider": self.code,
            "envelope_id": str(envelope.id),
            "voided": True,
        }


def get_signature_provider(code: str):
    normalized = (code or "crown_native").strip().lower()
    if normalized == "crown_native":
        return NativeSignatureProvider()
    raise ValueError("Signature provider is not configured.")
