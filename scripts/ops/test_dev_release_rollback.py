"""Offline, no-cloud tests for DEV prior-image capture and rollback safety."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dev_release_rollback as rollback

SHA = "a" * 40
DIGEST = "sha256:" + "b" * 64
IMAGE = "crownregistry.azurecr.io/crown2026:dev-" + SHA


def healthy(sha=SHA):
    return {"ok": True, "env": "dev", "db": "ok",
            "build_sha": sha, "artifact_build_sha": sha}


def fake_azure(*args, **kwargs):
    if args[:4] == ("webapp", "config", "appsettings", "list"):
        return [{"name": "BUILD_SHA", "value": SHA},
                {"name": "DEPLOY_RUN_ID", "value": "1234567890"},
                {"name": "DEPLOY_WORKFLOW", "value": "DEV Deploy (protected main)"},
                {"name": "DATABASE_URL", "value": "SENSITIVE_NOT_TO_BE_WRITTEN"}]
    if args[:3] == ("webapp", "config", "show"):
        return {"linuxFxVersion": "DOCKER|" + IMAGE}
    if args[:3] == ("acr", "repository", "show"):
        return {"digest": DIGEST}
    raise AssertionError(args)


class DevRollbackContracts(unittest.TestCase):
    def test_capture_and_restore_exact_digest_without_private_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            mutations = []
            with patch.object(rollback, "az", side_effect=lambda *a, **kw: (
                    mutations.append((a, kw)) if kw.get("json_mode") is False
                    else fake_azure(*a, **kw))), \
                 patch.object(rollback, "health", return_value=healthy()):
                evidence = rollback.capture(receipt)
                self.assertEqual(evidence["prior_sha"], SHA)
                self.assertEqual(evidence["prior_digest"], DIGEST)
                self.assertNotIn("SENSITIVE_NOT_TO_BE_WRITTEN", receipt.read_text())
                self.assertEqual(rollback.restore(receipt, sleep=lambda _: None), SHA)
            self.assertEqual(len(mutations), 3)
            self.assertIn(IMAGE.split(":dev-")[0] + "@" + DIGEST, mutations[0][0])
            self.assertIn("BUILD_SHA=" + SHA, mutations[1][0])
            self.assertNotIn("SENSITIVE_NOT_TO_BE_WRITTEN", str(mutations))

    def test_unknown_existing_image_fails_before_any_mutation(self):
        def wrong_image(*args, **kwargs):
            value = fake_azure(*args, **kwargs)
            if args[:3] == ("webapp", "config", "show"):
                return {"linuxFxVersion": "DOCKER|untrusted.registry.invalid/latest"}
            return value
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(rollback, "az", side_effect=wrong_image), \
             patch.object(rollback, "health", return_value=healthy()):
            with self.assertRaisesRegex(rollback.Unsafe, "prior_immutable_app_image_unverified"):
                rollback.capture(Path(directory) / "receipt.json")

    def test_unhealthy_previous_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(rollback, "az", side_effect=fake_azure), \
             patch.object(rollback, "health", return_value=healthy("c" * 40)):
            with self.assertRaisesRegex(rollback.Unsafe, "prior_dev_runtime_not_healthy"):
                rollback.capture(Path(directory) / "receipt.json")

    def test_malformed_receipts_never_modify_azure(self):
        valid = {"status": "CAPTURED", "prior_sha": SHA,
                 "prior_image": IMAGE, "prior_digest": DIGEST,
                 "prior_run_id": "1234567890",
                 "prior_workflow": "DEV Deploy (protected main)",
                 "captured_at_utc": "2026-11-14T13:00:00+00:00"}
        cases = [{"prior_sha": "bad"},
                 {"prior_digest": "sha256:untrusted"},
                 {"prior_image": "other.azurecr.io/other:latest"},
                 {"status": "UNVERIFIED"},
                 {"prior_run_id": None},
                 {"prior_workflow": "prod-deploy"},
                 {"unexpected_setting": "bad"}]
        for change in cases:
            with self.subTest(change=change):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory) / "receipt.json"
                    target.write_text(json.dumps({**valid, **change}), encoding="utf-8")
                    with patch.object(rollback, "az", side_effect=AssertionError("AZURE_CALLED")):
                        with self.assertRaises(rollback.Unsafe):
                            rollback.restore(target)

    def test_changed_acr_digest_denies_rollback_before_writes(self):
        valid = {"status": "CAPTURED", "prior_sha": SHA,
                 "prior_image": IMAGE, "prior_digest": DIGEST,
                 "prior_run_id": "1234567890",
                 "prior_workflow": "DEV Deploy (protected main)",
                 "captured_at_utc": "2026-11-14T13:00:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(valid), encoding="utf-8")
            with patch.object(rollback, "az", return_value={"digest": "sha256:" + "c"*64}):
                with self.assertRaisesRegex(rollback.Unsafe, "prior_image_digest_changed_or_unavailable"):
                    rollback.restore(path)


if __name__ == "__main__":
    unittest.main()
