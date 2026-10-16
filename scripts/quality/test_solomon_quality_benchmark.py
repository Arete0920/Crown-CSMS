"""Failure-mode tests for the offline Solomon benchmark runner."""
import unittest

from solomon_quality_benchmark import (
    BLOCKED_PROVIDER_STATUS,
    CATALOG_TOPICS,
    EXPECTED_TOPICS,
    SOURCE_DOCUMENT,
    evaluate_benchmark,
)


class SyntheticInputError(ValueError):
    pass


def fake_guidance(payload):
    if (type(payload) is not dict or set(payload) != {"topic", "human_review_acknowledged"}
            or type(payload["topic"]) is not str or payload["topic"] not in EXPECTED_TOPICS
            or payload["human_review_acknowledged"] is not True):
        raise SyntheticInputError
    topic = payload["topic"]
    return {
        "topic": topic, "title": "Synthetic title", "guidance": "Synthetic guidance",
        "source": "Synthetic maintained source", "policy_version": "synthetic-v1",
        "catalog_version": "synthetic-catalog-v1", "content_origin": "curated_internal",
        "mode": "curated_guidance", "human_review_required": True,
        "advisory_handoff": topic == "strategy",
        "external_provider_status": BLOCKED_PROVIDER_STATUS,
        "source_document": SOURCE_DOCUMENT,
        "source_section": topic if topic in CATALOG_TOPICS else "existing-guidance",
        "source_digest": "a" * 64,
        "steps": ["review"] if topic in CATALOG_TOPICS else [],
        "draft": "draft" if topic in CATALOG_TOPICS else "",
    }


def fake_external(payload):
    data = fake_guidance(payload)
    if data["topic"] == "strategy":
        raise SyntheticInputError
    return {"policy_version": data["policy_version"], "topic": data["topic"],
            "task": "Synthetic instruction", "source": {"title": data["title"], "guidance": data["guidance"]}}


def run(local=fake_guidance, external=fake_external, topics=EXPECTED_TOPICS, assistance=CATALOG_TOPICS):
    return evaluate_benchmark(guidance_topics=set(topics), assistance_topics=set(assistance),
                              local_guidance=local, build_external_payload=external,
                              input_error=SyntheticInputError)


class BenchmarkRunnerTests(unittest.TestCase):
    def test_expected_case_count_and_human_gate(self):
        result = run()
        self.assertEqual(result["automated_result"], "PASS")
        self.assertEqual(result["total"], 40)  # 2 inventory + 26 curated/gateway + 12 negative
        self.assertEqual(result["passed"], 40)
        self.assertEqual(result["certification"], "NOT_CERTIFIED")
        self.assertEqual(result["release_authority"], "HOLD_INDEPENDENT_HUMAN_REVIEW")

    def test_missing_topic_or_new_unapproved_topic_fails(self):
        for topics in (EXPECTED_TOPICS - {"quality"}, EXPECTED_TOPICS | {"unreviewed"}):
            result = run(topics=topics)
            self.assertEqual(result["automated_result"], "FAIL")
            self.assertIn("catalog:exact_topics", result["failed_case_ids"])

    def test_invalid_output_cannot_claim_approval(self):
        def unsafe(payload):
            return {**fake_guidance(payload), "human_review_required": False,
                    "external_provider_status": "enabled"}
        result = run(local=unsafe)
        self.assertEqual(result["automated_result"], "FAIL")
        self.assertIn("curated:quality", result["failed_case_ids"])

    def test_gateways_with_unreviewed_fields_fail(self):
        def unsafe(payload):
            return {**fake_external(payload), "raw_records": "synthetic"}
        result = run(external=unsafe)
        self.assertEqual(result["automated_result"], "FAIL")
        self.assertIn("gateway:quality", result["failed_case_ids"])

    def test_unsafe_input_acceptance_fails_without_echoing_content(self):
        def unsafe(payload):
            if type(payload) is dict and "prompt" in payload:
                return fake_guidance({"topic": "quality", "human_review_acknowledged": True})
            return fake_guidance(payload)
        result = run(local=unsafe)
        self.assertEqual(result["automated_result"], "FAIL")
        self.assertIn("reject:free_text", result["failed_case_ids"])
        self.assertNotIn("synthetic-injection", repr(result))

    def test_exception_does_not_convert_to_pass(self):
        def broken(payload):
            raise RuntimeError("synthetic error")
        result = run(local=broken)
        self.assertEqual(result["automated_result"], "FAIL")
        self.assertGreater(len(result["failed_case_ids"]), 0)


if __name__ == "__main__":
    unittest.main()
