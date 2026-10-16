"""Run the offline Solomon quality benchmark against production guidance functions.

This is source-test integration only: it does not activate any API or provider.
"""
from pathlib import Path
from runpy import run_path

from django.conf import settings
from django.test import SimpleTestCase

from solomon.assistance_catalog import ASSISTANCE
from solomon.guidance import (
    GUIDANCE,
    GuidanceInputError,
    build_external_payload,
    local_guidance,
)


class SolomonQualityBenchmarkTests(SimpleTestCase):
    def test_real_curated_guidance_contract_passes_offline_benchmark(self):
        repo_root = Path(settings.BASE_DIR).parent
        script = repo_root / "scripts/quality/solomon_quality_benchmark.py"
        evaluate = run_path(str(script))["evaluate_benchmark"]
        report = evaluate(
            guidance_topics=set(GUIDANCE),
            assistance_topics=set(ASSISTANCE),
            local_guidance=local_guidance,
            build_external_payload=build_external_payload,
            input_error=GuidanceInputError,
        )
        self.assertEqual(report["total"], 40, report)
        self.assertEqual(report["failed_case_ids"], [], report)
        self.assertEqual(report["automated_result"], "PASS", report)
        self.assertEqual(report["certification"], "NOT_CERTIFIED")
        self.assertEqual(report["release_authority"], "HOLD_INDEPENDENT_HUMAN_REVIEW")
