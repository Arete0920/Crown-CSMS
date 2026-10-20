"""Fail-closed regressions for C1 audit-bundle lifecycle governance.

These tests use synthetic index data only and never open signing keys.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "solomon_governance_c1"
    / "manage_bundle_lifecycle.py"
)


def _lifecycle_module():
    spec = importlib.util.spec_from_file_location(
        "crown_c1_lifecycle_test_module", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _index(active="synthetic-old"):
    return {
        "index_version": "1",
        "active_bundle": active,
        "certified_bundles": [
            {"bundle_id": "synthetic-old", "status": "active"}
        ],
        "superseded_bundles": [],
        "revoked_bundles": [],
    }


def test_active_bundle_revocation_clears_selection_without_replacement():
    lifecycle = _lifecycle_module()
    data = _index()
    saved = []

    with mock.patch.object(lifecycle, "load_index", return_value=data), mock.patch.object(
        lifecycle, "save_index", side_effect=lambda value: saved.append(value.copy())
    ):
        assert lifecycle.mark_revoked("synthetic-old", "key compromised") == 0

    assert len(saved) == 1
    assert data["active_bundle"] is None
    assert data["certified_bundles"][0]["status"] == "revoked"
    assert data["revoked_bundles"][0]["bundle_id"] == "synthetic-old"


def test_revoked_bundle_cannot_be_recertified():
    lifecycle = _lifecycle_module()
    data = _index(active=None)
    data["certified_bundles"][0]["status"] = "revoked"
    data["revoked_bundles"].append({"bundle_id": "synthetic-old"})
    with mock.patch.object(lifecycle, "load_index", return_value=data), mock.patch.object(
        lifecycle, "save_index"
    ) as save:
        assert lifecycle.mark_certified("synthetic-old") == 1
    save.assert_not_called()


def test_repeated_revocation_is_idempotent():
    lifecycle = _lifecycle_module()
    data = _index(active=None)
    data["certified_bundles"][0]["status"] = "revoked"
    data["revoked_bundles"].append({"bundle_id": "synthetic-old"})
    with mock.patch.object(lifecycle, "load_index", return_value=data), mock.patch.object(
        lifecycle, "save_index"
    ) as save:
        assert lifecycle.mark_revoked("synthetic-old") == 0
    assert len(data["revoked_bundles"]) == 1
    save.assert_not_called()


def test_revoking_unselected_bundle_preserves_other_active_selection():
    lifecycle = _lifecycle_module()
    data = _index(active="synthetic-new")
    with mock.patch.object(lifecycle, "load_index", return_value=data), mock.patch.object(
        lifecycle, "save_index"
    ) as save:
        assert lifecycle.mark_revoked("synthetic-old") == 0
    assert data["active_bundle"] == "synthetic-new"
    save.assert_called_once()


def test_security_held_bundle_cannot_be_promoted():
    lifecycle = _lifecycle_module()
    data = _index(active=None)
    data["certified_bundles"][0]["status"] = "quarantined"
    data["security_hold"] = {
        "bundle_id": "synthetic-old",
        "state": "quarantined_pending_operational_retirement",
    }
    with mock.patch.object(lifecycle, "load_index", return_value=data), mock.patch.object(
        lifecycle, "save_index"
    ) as save:
        assert lifecycle.mark_certified("synthetic-old") == 1
    save.assert_not_called()
