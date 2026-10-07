"""Tests for provider-neutral Solomon governed retrieval primitives."""

from datetime import date

from django.test import SimpleTestCase

from solomon.retrieval import (
    AuthorityDecision,
    RetrievalIntent,
    RetrievalRoute,
    SourceEvidence,
    build_cache_key,
    evaluate_answer_authority,
    select_retrieval_route,
    validate_source_evidence,
)


GOOD_DIGEST = "a" * 64
CACHE_SECRET = "test-only-cache-secret"


def evidence(**overrides):
    data = {
        "source_id": "C1-GOV-0001",
        "title": "Approved policy",
        "source_digest": GOOD_DIGEST,
        "source_version": "2026-10-06",
        "provenance_tier": "P1",
        "review_status": "APPROVED_CANONICAL",
        "rights_status": "owned",
        "rights_basis": "CROWN-owned canonical policy",
        "privacy_classification": "internal",
        "tenant_scope": "school-1",
        "role_scope": ("HEAD_OF_SCHOOL", "SUPPORT"),
        "effective_date": date(2026, 1, 1),
        "expires_on": date(2027, 1, 1),
        "reviewed_on": date(2026, 10, 1),
    }
    data.update(overrides)
    return SourceEvidence(**data)


class SolomonRetrievalRoutingTests(SimpleTestCase):
    def test_transactional_records_never_route_to_corpus(self):
        decision = select_retrieval_route(
            RetrievalIntent.TRANSACTIONAL_RECORD,
            retrieval_enabled=True,
        )
        self.assertEqual(decision.route, RetrievalRoute.STRUCTURED_SERVICE)

    def test_guidance_abstains_when_retrieval_disabled(self):
        decision = select_retrieval_route(
            RetrievalIntent.CANONICAL_GUIDANCE,
            retrieval_enabled=False,
        )
        self.assertEqual(decision.route, RetrievalRoute.ABSTAIN)

    def test_guidance_uses_cache_then_corpus_when_enabled(self):
        decision = select_retrieval_route(
            RetrievalIntent.CANONICAL_GUIDANCE,
            retrieval_enabled=True,
        )
        self.assertEqual(decision.route, RetrievalRoute.CACHE_THEN_CORPUS)

    def test_aggregate_analysis_is_separately_gated(self):
        denied = select_retrieval_route(
            RetrievalIntent.AGGREGATE_ANALYSIS,
            retrieval_enabled=True,
            aggregate_retrieval_enabled=False,
        )
        allowed = select_retrieval_route(
            RetrievalIntent.AGGREGATE_ANALYSIS,
            retrieval_enabled=True,
            aggregate_retrieval_enabled=True,
        )
        self.assertEqual(denied.route, RetrievalRoute.ABSTAIN)
        self.assertEqual(allowed.route, RetrievalRoute.STRUCTURED_THEN_CORPUS)


class SolomonRetrievalEvidenceTests(SimpleTestCase):
    def test_valid_source_evidence_passes(self):
        result = validate_source_evidence(
            evidence(),
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            as_of=date(2026, 10, 6),
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.reasons, ())

    def test_source_evidence_fails_closed_on_scope_rights_and_freshness(self):
        result = validate_source_evidence(
            evidence(
                tenant_scope="school-2",
                rights_status="unknown",
                expires_on=date(2026, 10, 1),
            ),
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            as_of=date(2026, 10, 6),
        )
        self.assertFalse(result.valid)
        self.assertIn("tenant_scope_mismatch", result.reasons)
        self.assertIn("unapproved_rights_status", result.reasons)
        self.assertIn("expired", result.reasons)

    def test_missing_rights_basis_fails(self):
        result = validate_source_evidence(
            evidence(rights_basis=""),
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            as_of=date(2026, 10, 6),
        )
        self.assertFalse(result.valid)
        self.assertIn("missing_rights_basis", result.reasons)

    def test_missing_review_date_fails(self):
        result = validate_source_evidence(
            evidence(reviewed_on=None),
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            as_of=date(2026, 10, 6),
        )
        self.assertFalse(result.valid)
        self.assertIn("missing_review_date", result.reasons)

    def test_wrong_role_fails(self):
        result = validate_source_evidence(
            evidence(),
            tenant_id="school-1",
            role="TEACHER",
            as_of=date(2026, 10, 6),
        )
        self.assertFalse(result.valid)
        self.assertIn("role_scope_mismatch", result.reasons)

    def test_superseded_source_fails(self):
        result = validate_source_evidence(
            evidence(superseded_by="C1-GOV-0042"),
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            as_of=date(2026, 10, 6),
        )
        self.assertFalse(result.valid)
        self.assertIn("superseded_source", result.reasons)


class SolomonAnswerAuthorityGateTests(SimpleTestCase):
    def test_allows_grounded_answer_with_valid_evidence(self):
        result = evaluate_answer_authority(
            [evidence()],
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            citations_present=True,
            as_of=date(2026, 10, 6),
        )
        self.assertEqual(result.decision, AuthorityDecision.ALLOW)

    def test_abstains_without_citations(self):
        result = evaluate_answer_authority(
            [evidence()],
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            citations_present=False,
            as_of=date(2026, 10, 6),
        )
        self.assertEqual(result.decision, AuthorityDecision.ABSTAIN)
        self.assertIn("citations_missing", result.reasons)

    def test_abstains_on_restricted_data(self):
        result = evaluate_answer_authority(
            [evidence()],
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            citations_present=True,
            restricted_data_detected=True,
            as_of=date(2026, 10, 6),
        )
        self.assertEqual(result.decision, AuthorityDecision.ABSTAIN)
        self.assertIn("restricted_data_detected", result.reasons)

    def test_abstains_on_consequential_domain(self):
        result = evaluate_answer_authority(
            [evidence()],
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            citations_present=True,
            consequential_decision_domain="financial_aid",
            as_of=date(2026, 10, 6),
        )
        self.assertEqual(result.decision, AuthorityDecision.ABSTAIN)
        self.assertIn(
            "consequential_decision_requires_human_authority",
            result.reasons,
        )

    def test_requires_human_review_when_configured(self):
        result = evaluate_answer_authority(
            [evidence()],
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            citations_present=True,
            human_review_required=True,
            human_review_acknowledged=False,
            as_of=date(2026, 10, 6),
        )
        self.assertEqual(result.decision, AuthorityDecision.HUMAN_REVIEW)

    def test_cache_key_is_deterministic_and_does_not_include_raw_question(self):
        question = "What is our approved re-enrollment policy?"
        first = build_cache_key(
            tenant_id="school-1",
            role="HEAD_OF_SCHOOL",
            topic="reenrollment",
            corpus_version="7",
            policy_version="2",
            question=question,
            cache_key_secret=CACHE_SECRET,
        )
        second = build_cache_key(
            tenant_id="school-1",
            role="head_of_school",
            topic="REENROLLMENT",
            corpus_version="7",
            policy_version="2",
            question="  What   is our approved re-enrollment policy? ",
            cache_key_secret=CACHE_SECRET,
        )
        self.assertEqual(first, second)
        self.assertNotIn("re-enrollment", first)
        self.assertTrue(first.startswith("solomon:retrieval:v1:"))

    def test_cache_key_requires_secret(self):
        with self.assertRaises(ValueError):
            build_cache_key(
                tenant_id="school-1",
                role="HEAD_OF_SCHOOL",
                topic="reenrollment",
                corpus_version="7",
                policy_version="2",
                question="What is our policy?",
                cache_key_secret="",
            )

    def test_cache_key_changes_with_secret(self):
        common = {
            "tenant_id": "school-1",
            "role": "HEAD_OF_SCHOOL",
            "topic": "reenrollment",
            "corpus_version": "7",
            "policy_version": "2",
            "question": "What is our policy?",
        }
        first = build_cache_key(**common, cache_key_secret="secret-a")
        second = build_cache_key(**common, cache_key_secret="secret-b")
        self.assertNotEqual(first, second)
