"""Public Heritage sales sandbox must never ship credential prefill artifacts."""
from pathlib import Path


def test_heritage_passwordless_sandbox_has_no_public_credential_manifest():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "backend/core/demo/heritage_demo_credentials.json").exists()
    policy = (root / "docs/DEMO_MODE_POLICY.md").read_text(encoding="utf-8")
    assert "public credential manifests" in policy
