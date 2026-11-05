"""Negative and positive checks for the ISO Annex A claim integrity guard."""

from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from verify_iso27001_soa import COLUMNS, EXPECTED, validate_text, main

DEFAULT = {
    "normative_title": "REFER_TO_LICENSED_STANDARD",
    "normative_reference_validation": "PENDING_AUTHORIZED_REVIEW",
    "applicability": "UNASSESSED",
    "applicability_justification_or_exclusion": "PENDING_SCOPE_RISK_AND_SOURCE_REVIEW",
    "identified_risk_ids": "UNMAPPED",
    "risk_treatment_decision": "UNDECIDED",
    "implementation_status": "NOT_ASSESSED",
    "proposed_responsible_role": "Proposed ISMS management",
    "appointed_control_owner": "UNASSIGNED",
    "control_frequency": "TO_BE_DEFINED",
    "evidence_reference": "NONE_LINKED",
    "evidence_stage": "NOT_ASSESSED",
    "operating_test": "NOT_DEFINED",
    "findings": "NOT_ASSESSED",
    "independent_reviewer": "UNASSIGNED",
    "management_approval": "NOT_APPROVED",
    "review_date": "NOT_REVIEWED",
    "related_soc2_evidence": "UNMAPPED",
    "next_decision": "Confirm normative source and actual applicability",
}


def template():
    return [dict(DEFAULT, annex_a_id=key, control_family=family)
            for key, family in EXPECTED.items()]


def csv_content(rows, header=COLUMNS):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=header, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


class IsoSoaGuardTests(unittest.TestCase):
    def check_problem(self, change, fragment):
        rows = template()
        change(rows)
        self.assertTrue(any(fragment in issue for issue in validate_text(csv_content(rows))), fragment)

    def test_initial_unassessed_93_control_intake_passes(self):
        self.assertEqual(validate_text(csv_content(template())), [])

    def test_reordered_rows_remain_valid(self):
        self.assertEqual(validate_text(csv_content(list(reversed(template())))), [])

    def test_missing_control_fails(self):
        self.check_problem(lambda r: r.pop(), "expected 93")

    def test_duplicate_control_fails(self):
        self.check_problem(lambda r: r[-1].update(annex_a_id="A.5.1"), "duplicate")

    def test_unknown_control_fails(self):
        self.check_problem(lambda r: r[0].update(annex_a_id="A.5.38"), "unknown")

    def test_family_mismatch_fails(self):
        self.check_problem(lambda r: r[0].update(control_family="People"), "control_family")

    def test_unexpected_column_fails(self):
        self.assertIn("columns", validate_text(csv_content(template(), header=COLUMNS[:-1]))[0])

    def test_formula_injection_fails(self):
        self.check_problem(lambda r: r[0].update(next_decision="=1+1"), "formula injection")

    def test_unsanctioned_applicability_value_fails(self):
        self.check_problem(lambda r: r[0].update(applicability="COMPLIANT"), "invalid applicability")

    def test_applied_without_source_fails(self):
        self.check_problem(lambda r: r[0].update(applicability="APPLICABLE"), "authorized source review")

    def test_excluded_without_justification_fails(self):
        self.check_problem(lambda r: r[0].update(
            applicability="NOT_APPLICABLE",
            normative_reference_validation="AUTHORIZED_REVIEW_COMPLETE",
            independent_reviewer="Security reviewer",
            risk_treatment_decision="Review accepted exclusions",
            review_date="2026-10-28", evidence_reference="SOURCE-REVIEW-01",
        ), "lacks justification")

    def test_approval_without_evidence_fails(self):
        self.check_problem(lambda r: r[0].update(management_approval="APPROVED"), "unassessed control")

    def test_source_review_needs_reviewer(self):
        self.check_problem(lambda r: r[0].update(
            normative_reference_validation="AUTHORIZED_REVIEW_COMPLETE"
        ), "source validation needs a named reviewer")

    def test_source_implementation_requires_owner_and_evidence(self):
        self.check_problem(lambda r: r[0].update(
            implementation_status="SOURCE_IMPLEMENTED"
        ), "claimed implementation needs an appointed owner")

    def test_runtime_verification_requires_actual_runtime_stage(self):
        self.check_problem(lambda r: r[0].update(
            implementation_status="RUNTIME_VERIFIED", evidence_reference="EVID-1",
            appointed_control_owner="Operations lead"
        ), "runtime claim needs runtime evidence stage")

    def test_operating_evidence_requires_findings(self):
        self.check_problem(lambda r: r[0].update(
            evidence_stage="O", evidence_reference="EVID-1", operating_test="Review event population",
            review_date="2026-10-28"
        ), "operating/assurance claim needs findings disposition")

    def test_independent_assurance_requires_reviewer(self):
        self.check_problem(lambda r: r[0].update(
            evidence_stage="E", evidence_reference="EVID-1", operating_test="Review examination outcome",
            review_date="2026-10-28", findings="No findings"
        ), "independent assurance needs named reviewer")

    def test_review_date_must_be_calendar_valid(self):
        self.check_problem(lambda r: r[0].update(
            evidence_stage="S", evidence_reference="EVID-1", operating_test="Verify source checks",
            review_date="2026-02-30"
        ), "valid review date")

    def test_valid_reviewed_applicability_without_certification(self):
        rows = template()
        rows[0].update(
            normative_reference_validation="AUTHORIZED_REVIEW_COMPLETE",
            independent_reviewer="ISO control reviewer",
            applicability="APPLICABLE",
            applicability_justification_or_exclusion="Risk identified for credential misuse",
            risk_treatment_decision="Mitigate credential misuse",
            review_date="2026-10-28", evidence_reference="SOURCE-REVIEW-01",
        )
        self.assertEqual(validate_text(csv_content(rows)), [])

    def test_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(main(["--path", str(Path(td) / "no.csv")]), 1)


    def test_repository_policy_never_skips_absent_register(self):
        workflow = (
            Path(__file__).resolve().parents[2]
            / ".github" / "workflows" / "repository-policy.yml"
        ).read_text(encoding="utf-8")
        name = "- name: Validate ISO 27001 Annex A intake and claims"
        self.assertEqual(workflow.count(name), 1)
        step = workflow.split(name, 1)[1].split("      - name:", 1)[0]
        self.assertIn("python tools/ci/verify_iso27001_soa.py", step)
        self.assertNotIn("if [ -f", step)
        self.assertNotIn("continue-on-error", step)
        self.assertNotIn("|| true", step)
        self.assertNotIn("      if:", step)


if __name__ == "__main__":
    unittest.main()
