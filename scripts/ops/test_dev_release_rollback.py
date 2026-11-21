"""Offline, no-cloud tests for DEV prior-image capture and rollback safety."""
import json
import os
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
                {"name": "WEBSITES_PORT", "value": "8000"},
                {"name": "CROWN_ENV", "value": "dev"},
                {"name": "DJANGO_ENV", "value": "development"},
                {"name": "ENVIRONMENT", "value": "dev"},
                {"name": "DATABASE_URL", "value": "SENSITIVE_NOT_TO_BE_WRITTEN"}]
    if args[:3] == ("webapp", "config", "show"):
        return {"linuxFxVersion": "DOCKER|" + IMAGE}
    if args[:3] == ("acr", "repository", "show"):
        return {"digest": DIGEST}
    raise AssertionError(args)


class DevRollbackContracts(unittest.TestCase):
    def test_capture_and_restore_exact_digest_without_private_settings(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}):
            receipt = Path(directory) / "crown-dev-auto-rollback.json"
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

    def test_capture_requires_pinned_image_to_match_the_sha_tag_digest(self):
        for configured_digest in (DIGEST, "sha256:" + "c" * 64):
            with self.subTest(configured_digest=configured_digest):
                def digest_pinned_azure(*args, **kwargs):
                    if args[:3] == ("webapp", "config", "show"):
                        return {"linuxFxVersion": (
                            "DOCKER|crownregistry.azurecr.io/crown2026@" + configured_digest
                        )}
                    return fake_azure(*args, **kwargs)

                with (
                    tempfile.TemporaryDirectory() as directory,
                    patch.dict(os.environ, {"RUNNER_TEMP": directory}),
                    patch.object(rollback, "az", side_effect=digest_pinned_azure),
                    patch.object(rollback, "health", return_value=healthy()),
                ):
                    receipt = Path(directory) / "crown-dev-auto-rollback.json"
                    if configured_digest == DIGEST:
                        evidence = rollback.capture(receipt)
                        self.assertEqual(evidence["prior_image"], IMAGE)
                        self.assertEqual(evidence["prior_digest"], DIGEST)
                    else:
                        with self.assertRaises(rollback.Unsafe):
                            rollback.capture(receipt)
                        self.assertFalse(receipt.exists())

    def test_unknown_existing_image_fails_before_any_mutation(self):
        def wrong_image(*args, **kwargs):
            value = fake_azure(*args, **kwargs)
            if args[:3] == ("webapp", "config", "show"):
                return {"linuxFxVersion": "DOCKER|untrusted.registry.invalid/latest"}
            return value
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(rollback, "az", side_effect=wrong_image), \
             patch.object(rollback, "health", return_value=healthy()):
            with self.assertRaisesRegex(rollback.Unsafe, "prior_immutable_app_image_unverified"):
                rollback.capture(Path(directory) / "crown-dev-auto-rollback.json")

    def test_prior_runtime_configuration_drift_blocks_before_mutation(self):
        def unsafe_config(*args, **kwargs):
            values = fake_azure(*args, **kwargs)
            if args[:4] == ("webapp", "config", "appsettings", "list"):
                for row in values:
                    if row["name"] == "WEBSITES_PORT":
                        row["value"] = "9000"
            return values
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(rollback, "az", side_effect=unsafe_config), \
             patch.object(rollback, "health", return_value=healthy()):
            with self.assertRaisesRegex(rollback.Unsafe, "prior_runtime_settings_not_rollback_compatible"):
                rollback.capture(Path(directory) / "crown-dev-auto-rollback.json")

    def test_unhealthy_previous_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(rollback, "az", side_effect=fake_azure), \
             patch.object(rollback, "health", return_value=healthy("c" * 40)):
            with self.assertRaisesRegex(rollback.Unsafe, "prior_dev_runtime_not_healthy"):
                rollback.capture(Path(directory) / "crown-dev-auto-rollback.json")

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
                with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}):
                    target = Path(directory) / "crown-dev-auto-rollback.json"
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
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}):
            path = Path(directory) / "crown-dev-auto-rollback.json"
            path.write_text(json.dumps(valid), encoding="utf-8")
            with patch.object(rollback, "az", return_value={"digest": "sha256:" + "c"*64}):
                with self.assertRaisesRegex(rollback.Unsafe, "prior_image_digest_changed_or_unavailable"):
                    rollback.restore(path)


    def test_receipt_path_rejects_outside_and_untrusted_cli_paths_before_azure(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
            patch.dict(os.environ, {"RUNNER_TEMP": directory}),
            patch.object(rollback, "az", side_effect=AssertionError("AZURE_CALLED")),
        ):
            root = Path(directory)
            rejected = (
                root / "unexpected.json",
                Path(outside) / "crown-dev-auto-rollback.json",
                root / "nested" / "crown-dev-auto-rollback.json",
                Path("../crown-dev-auto-rollback.json"),
            )
            for target in rejected:
                with self.subTest(target=str(target)):
                    with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_path_invalid"):
                        rollback.capture(target)
                    with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_path_invalid"):
                        rollback.restore(target)

            with patch.dict(os.environ, {"RUNNER_TEMP": ""}):
                with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_path_invalid"):
                    rollback.capture(root / "crown-dev-auto-rollback.json")

    def test_symlinked_receipt_is_rejected_without_azure_calls(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
            patch.dict(os.environ, {"RUNNER_TEMP": directory}),
            patch.object(rollback, "az", side_effect=AssertionError("AZURE_CALLED")),
        ):
            target = Path(directory) / "crown-dev-auto-rollback.json"
            external = Path(outside) / "external.json"
            external.write_text("private", encoding="utf-8")
            try:
                target.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not supported on this runner")
            with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_path_invalid"):
                rollback.capture(target)
            with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_path_invalid"):
                rollback.restore(target)
            self.assertEqual(external.read_text(encoding="utf-8"), "private")

    def test_restore_rejects_oversized_and_non_regular_receipts_without_azure(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"RUNNER_TEMP": directory}),
            patch.object(rollback, "az", side_effect=AssertionError("AZURE_CALLED")),
        ):
            target = Path(directory) / "crown-dev-auto-rollback.json"
            target.write_text(" " * 4097, encoding="utf-8")
            with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_too_large"):
                rollback.restore(target)
            target.unlink()
            target.mkdir()
            with self.assertRaisesRegex(rollback.Unsafe, "rollback_receipt_not_regular"):
                rollback.restore(target)


if __name__ == "__main__":
    unittest.main()
