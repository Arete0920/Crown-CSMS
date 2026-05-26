import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "verify_public_surface_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_public_surface_policy", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _configure_repo(module, tmp_path: Path) -> tuple[Path, Path, Path]:
    backend = tmp_path / "backend"
    public_policy = tmp_path / "docs" / "security" / "public_endpoint_policy_matrix.json"
    csrf_policy = tmp_path / "docs" / "security" / "csrf_exception_policy_matrix.json"
    backend.mkdir(parents=True)
    public_policy.parent.mkdir(parents=True, exist_ok=True)
    csrf_policy.parent.mkdir(parents=True, exist_ok=True)

    module.ROOT = tmp_path
    module.BACKEND = backend
    module.PUBLIC_POLICY = public_policy
    module.CSRF_POLICY = csrf_policy
    return backend, public_policy, csrf_policy


def _write_policy(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"version": "test", "entries": entries}, indent=2), encoding="utf-8")


def test_public_surface_policy_gate_passes_for_matching_inventory(tmp_path, capsys):
    module = _load_module()
    backend, public_policy, csrf_policy = _configure_repo(module, tmp_path)

    sample = backend / "sample_views.py"
    sample.write_text(
        "@permission_classes([AllowAny])\n"
        "def public_view(request):\n"
        "    return None\n\n"
        "@csrf_exempt\n"
        "def webhook(request):\n"
        "    return None\n",
        encoding="utf-8",
    )

    _write_policy(
        public_policy,
        [
            {
                "type": "allow_any",
                "path": "backend/sample_views.py",
                "symbol": "public_view",
                "status": "approved",
                "owner": "Platform Security",
                "rationale": "Public endpoint under test.",
                "controls": ["Read-only output"],
            }
        ],
    )
    _write_policy(
        csrf_policy,
        [
            {
                "type": "csrf_exempt",
                "path": "backend/sample_views.py",
                "symbol": "webhook",
                "status": "approved",
                "owner": "Platform Security",
                "rationale": "Webhook under test.",
                "controls": ["Signature validation"],
            }
        ],
    )

    assert module.main() == 0
    out = capsys.readouterr().out
    assert "Public surface policy gate PASSED" in out
    assert "AllowAny entries tracked: 1" in out
    assert "csrf_exempt entries tracked: 1" in out


def test_public_surface_policy_gate_fails_on_unmanaged_entry(tmp_path, capsys):
    module = _load_module()
    backend, public_policy, csrf_policy = _configure_repo(module, tmp_path)

    (backend / "sample_views.py").write_text(
        "@permission_classes([AllowAny])\n"
        "def public_view(request):\n"
        "    return None\n",
        encoding="utf-8",
    )

    _write_policy(public_policy, [])
    _write_policy(csrf_policy, [])

    assert module.main() == 1
    out = capsys.readouterr().out
    assert "AllowAny: unmanaged entries detected (1):" in out
    assert "backend/sample_views.py::public_view" in out


def test_public_surface_policy_gate_fails_on_stale_entry(tmp_path, capsys):
    module = _load_module()
    _, public_policy, csrf_policy = _configure_repo(module, tmp_path)

    _write_policy(
        public_policy,
        [
            {
                "type": "allow_any",
                "path": "backend/sample_views.py",
                "symbol": "public_view",
                "status": "approved",
                "owner": "Platform Security",
                "rationale": "Stale entry under test.",
                "controls": ["Read-only output"],
            }
        ],
    )
    _write_policy(csrf_policy, [])

    assert module.main() == 1
    out = capsys.readouterr().out
    assert "AllowAny: stale policy entries detected (1):" in out
    assert "backend/sample_views.py::public_view" in out


def test_public_surface_policy_gate_fails_on_invalid_policy_entry(tmp_path, capsys):
    module = _load_module()
    _, public_policy, csrf_policy = _configure_repo(module, tmp_path)

    _write_policy(
        public_policy,
        [
            {
                "type": "allow_any",
                "path": "backend/sample_views.py",
                "symbol": "public_view",
                "status": "approved",
                "owner": "Platform Security",
                "rationale": "Malformed entry under test."
            }
        ],
    )
    _write_policy(csrf_policy, [])

    assert module.main() == 1
    out = capsys.readouterr().out
    assert "Public surface policy gate FAILED:" in out
    assert "Missing key 'controls'" in out
