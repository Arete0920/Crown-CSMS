"""Synthetic validator tests; fixtures are never operational release proof."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from tools.validate_release_runtime_evidence import validate


class RuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "manifest.json"
        self.sha = "a" * 40
        self.now = datetime.now(timezone.utc)
        self.keys = ["first", "second"]
        self.criteria = ["authorized", "tenant_isolated"]
        self.payload = {
            "schema_version": "1.0", "source_sha": self.sha,
            "backend_sha": self.sha, "frontend_sha": self.sha,
            "environment": "staging", "runtime_id": "synthetic-fixture-runtime",
            "run_reference": "synthetic-fixture-run", "operator_reference": "synthetic-fixture-operator",
            "started_at": (self.now - timedelta(minutes=10)).isoformat(),
            "completed_at": (self.now - timedelta(minutes=1)).isoformat(),
            "gates": {"domain-model": {"junit_path": "report.xml", "records": [
                {"key": key, "proofs": {criterion: ["fixture." + key, criterion] for criterion in self.criteria}}
                for key in self.keys
            ]}}
        }
        self.report = ET.Element("testsuite", tests="4", failures="0", errors="0", skipped="0")
        props = ET.SubElement(self.report, "properties")
        for field in ("source_sha", "backend_sha", "frontend_sha", "environment", "runtime_id", "run_reference"):
            ET.SubElement(props, "property", name=field, value=self.payload[field])
        for key in self.keys:
            for criterion in self.criteria:
                ET.SubElement(self.report, "testcase", classname="fixture." + key, name=criterion)

    def write(self):
        content = ET.tostring(self.report)
        (self.root / "report.xml").write_bytes(content)
        group = next(iter(self.payload["gates"].values()))
        group["junit_sha256"] = hashlib.sha256(content).hexdigest()
        self.path.write_text(json.dumps(self.payload))

    def result(self, **kwargs):
        self.write()
        return validate(self.path, self.sha, "staging", next(iter(self.payload["gates"])),
                        self.keys, self.criteria, now=self.now, **kwargs)

    def test_complete_current_fixture_is_accepted(self):
        self.assertTrue(self.result()["pass"])

    def test_absent_packet_fails_closed(self):
        self.assertFalse(validate(self.path, self.sha, "staging", "domain-model", self.keys, self.criteria)["pass"])

    def test_all_deployed_identities_must_match(self):
        for field in ("source_sha", "backend_sha", "frontend_sha"):
            with self.subTest(field=field):
                self.payload[field] = "b" * 40
                self.assertFalse(self.result()["pass"])
                self.payload[field] = self.sha

    def test_wrong_environment_is_rejected(self):
        self.payload["environment"] = "production"
        self.assertFalse(self.result()["pass"])

    def test_unidentified_runtime_is_rejected(self):
        for field in ("runtime_id", "run_reference", "operator_reference"):
            saved = self.payload[field]
            self.payload[field] = ""
            self.assertFalse(self.result()["pass"])
            self.payload[field] = saved

    def test_stale_or_future_or_unfinished_evidence_is_rejected(self):
        for started, completed in [(self.now - timedelta(days=2), self.now - timedelta(days=1)),
                                   (self.now, self.now + timedelta(seconds=1)),
                                   (self.now - timedelta(seconds=1), self.now - timedelta(seconds=2))]:
            self.payload["started_at"], self.payload["completed_at"] = started.isoformat(), completed.isoformat()
            self.assertFalse(self.result()["pass"])

    def test_naive_timestamp_is_rejected(self):
        self.payload["started_at"] = "2026-10-06T00:00:00"
        self.assertFalse(self.result()["pass"])

    def test_failed_error_and_skipped_cases_are_rejected(self):
        case = self.report.find("testcase")
        for tag in ("failure", "error", "skipped"):
            child = ET.SubElement(case, tag)
            self.assertFalse(self.result()["pass"])
            case.remove(child)

    def test_declared_suite_failures_are_rejected(self):
        self.report.set("errors", "1")
        self.assertFalse(self.result()["pass"])

    def test_declared_aggregate_failures_are_rejected(self):
        self.report.tag = "testsuites"
        self.assertTrue(self.result()["pass"])
        for field in ("failures", "errors", "skipped", "disabled"):
            with self.subTest(field=field):
                self.report.set(field, "1")
                self.assertFalse(self.result()["pass"])
                self.report.set(field, "0")

    def test_duplicate_identity_properties_are_rejected(self):
        props = self.report.find("properties")
        ET.SubElement(props, "property", name="source_sha", value=self.sha)
        self.assertFalse(self.result()["pass"])

    def test_incomplete_or_duplicate_control_coverage_is_rejected(self):
        records = self.payload["gates"]["domain-model"]["records"]
        records.pop()
        self.assertFalse(self.result()["pass"])
        records.append(records[0])
        self.assertFalse(self.result()["pass"])

    def test_missing_criterion_is_rejected(self):
        del self.payload["gates"]["domain-model"]["records"][0]["proofs"]["authorized"]
        self.assertFalse(self.result()["pass"])

    def test_nonexistent_or_reused_testcase_is_rejected(self):
        proofs = self.payload["gates"]["domain-model"]["records"][0]["proofs"]
        proofs["authorized"] = ["missing", "missing"]
        self.assertFalse(self.result()["pass"])
        proofs["authorized"] = proofs["tenant_isolated"]
        self.assertFalse(self.result()["pass"])

    def test_duplicate_testcases_are_rejected(self):
        ET.SubElement(self.report, "testcase", classname="fixture.first", name="authorized")
        self.assertFalse(self.result()["pass"])

    def test_report_identity_mismatch_is_rejected(self):
        self.report.find("properties/property").set("value", "b" * 40)
        self.assertFalse(self.result()["pass"])

    def test_packet_path_traversal_is_rejected(self):
        self.payload["gates"]["domain-model"]["junit_path"] = "../outside.xml"
        self.assertFalse(self.result()["pass"])

    def test_tampered_report_is_rejected(self):
        self.write()
        (self.root / "report.xml").write_text("<testsuite/>")
        self.assertFalse(validate(self.path, self.sha, "staging", "domain-model", self.keys, self.criteria, now=self.now)["pass"])

    def test_duplicate_json_keys_are_rejected(self):
        self.write()
        self.path.write_text('{"schema_version":"1.0","schema_version":"1.0"}')
        self.assertFalse(validate(self.path, self.sha, "staging", "domain-model", self.keys, self.criteria)["pass"])

    def test_boolean_pass_claim_cannot_replace_executed_proof(self):
        self.payload["gates"]["domain-model"] = {"pass": True, "records": []}
        self.assertFalse(self.result()["pass"])

    def test_empty_control_inventory_cannot_pass(self):
        self.write()
        self.assertFalse(validate(self.path, self.sha, "staging", "domain-model", [], [], now=self.now)["pass"])

    def performance(self):
        self.keys, self.criteria = ["first"], ["load_test"]
        self.payload["gates"] = {"performance": {"junit_path": "report.xml", "records": [{
            "key": "first", "proofs": {"load_test": ["fixture.first", "load_test"]},
            "measured": {"users": 20, "p95_ms": 50, "error_rate": 0},
            "accepted_targets": {"users": 10, "p95_ms": 100, "error_rate": 0},
            "target_approval_reference": "synthetic-fixture-approval",
        }]}}
        for case in self.report.findall("testcase"):
            self.report.remove(case)
        case = ET.SubElement(self.report, "testcase", classname="fixture.first", name="load_test")
        props = ET.SubElement(case, "properties")
        for key, value in self.payload["gates"]["performance"]["records"][0]["measured"].items():
            ET.SubElement(props, "property", name=key, value=str(value))
        return self.payload["gates"]["performance"]["records"][0]

    def test_measured_performance_must_match_report_and_targets(self):
        record = self.performance()
        self.assertTrue(self.result()["pass"])
        record["measured"]["p95_ms"] = 101
        self.assertFalse(self.result()["pass"])
        record["measured"]["p95_ms"] = 51
        self.assertFalse(self.result()["pass"])

    def test_performance_requires_accepted_targets(self):
        record = self.performance()
        del record["target_approval_reference"]
        self.assertFalse(self.result()["pass"])

    def test_duplicate_measurement_properties_are_rejected(self):
        self.performance()
        props = self.report.find("testcase/properties")
        ET.SubElement(props, "property", name="p95_ms", value="50")
        self.assertFalse(self.result()["pass"])

    def test_performance_rejects_boolean_and_nonfinite_measurements(self):
        record = self.performance()
        for value in (True, float("nan"), float("inf"), -1):
            record["measured"]["users"] = value
            self.assertFalse(self.result()["pass"])

    def test_wrong_schema_and_malformed_packet_are_rejected(self):
        self.payload["schema_version"] = "other"
        self.assertFalse(self.result()["pass"])
        self.path.write_text("not JSON")
        self.assertFalse(validate(self.path, self.sha, "staging", "domain-model", self.keys, self.criteria)["pass"])


if __name__ == "__main__":
    unittest.main()
