import os
from unittest.mock import patch

from django.test import SimpleTestCase

from crown_api import version_views


class VersionBuildShaTests(SimpleTestCase):
    def test_build_sha_environment_is_authoritative(self):
        full_sha = "a" * 40
        runtime = {"BUILD_SHA": full_sha, "GITHUB_SHA": "b" * 40}
        with patch.dict(os.environ, runtime, clear=False):
            self.assertEqual(version_views._resolve_build_sha(), full_sha)

    def test_github_sha_is_secondary_runtime_source(self):
        full_sha = "b" * 40
        with patch.dict(os.environ, {"GITHUB_SHA": full_sha}, clear=False):
            os.environ.pop("BUILD_SHA", None)
            self.assertEqual(version_views._resolve_build_sha(), full_sha)

    def test_baked_sha_is_only_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(version_views, "BAKED_BUILD_SHA", "abc1234"):
                self.assertEqual(version_views._resolve_build_sha(), "abc1234")

    def test_public_version_endpoint_returns_full_runtime_sha(self):
        full_sha = "c" * 40
        with patch.dict(os.environ, {"BUILD_SHA": full_sha}, clear=False):
            response = self.client.get("/api/v1/version/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["build_sha"], full_sha)
