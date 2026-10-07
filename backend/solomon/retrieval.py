"""Provider-neutral governed retrieval primitives for CROWN Solomon.

This module deliberately performs no network calls, embedding work, vector writes,
or generated-response calls. It defines the decision contracts that future
retrieval implementations must satisfy before activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Iterable, Sequence


class RetrievalIntent(str, Enum):
    CANONICAL_GUIDANCE = "canonical_guidance"
    TRANSACTIONAL_RECORD = "transactional_record"
    AGGREGATE_ANALYSIS = "aggregate_analysis"
    UNSUPPORTED = "unsupported"


class RetrievalRoute(str, Enum):
    CACHE_THEN_CORPUS = "cache_then_corpus"
    STRUCTURED_SERVICE = "structured_service"
    STRUCTURED_THEN_CORPUS = "structured_then_corpus"
    ABSTAIN = "abstain"


class AuthorityDecision(str, Enum):
    ALLOW = "allow"
    HUMAN_REVIEW = "human_review"
    ABSTAIN = "abstain"


APPROVED_REVIEW_STATES = frozenset(
    {
        "APPROVED_CANONICAL",
        "APPROVED_REFERENCE_ONLY",
    }
)
APPROVED_PROVENANCE_TIERS = frozenset({"P0", "P1", "P2"})
APPROVED_RIGHTS_STATUSES = frozenset({"owned", "licensed", "approved_use"})
APPROVED_PRIVACY_CLASSES = frozenset({"public", "internal"})
PROHIBITED_DECISION_DOMAINS = frozenset(
    {
        "admissions",
        "grading",
        "discipline",
        "financial_aid",
        "health",
        "safeguarding",
        "pastoral",
    }
)
HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RetrievalDecision:
    route: RetrievalRoute
    reason: str


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """Minimum evidence contract for a retrievable Solomon source."""

    source_id: str
    title: str
    source_digest: str
    source_version: str
    provenance_tier: str
    review_status: str
    rights_status: str
    privacy_classification: str
    tenant_scope: str
    role_scope: tuple[str, ...] = ()
    effective_date: date | None = None
    expires_on: date | None = None
    reviewed_on: date | None = None
    supersedes: str = ""


@dataclass(frozen=True, slots=True)
class SourceValidation:
    valid: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthorityGateResult:
    decision: AuthorityDecision
    reasons: tuple[str, ...]


def select_retrieval_route(
    intent: RetrievalIntent,
    *,
    retrieval_enabled: bool,
    aggregate_retrieval_enabled: bool = False,
) -> RetrievalDecision:
    """Select the narrowest data path for the request.

    Structured system-of-record queries never route through semantic retrieval.
    Aggregate analysis stays closed until its separate disclosure controls are
    explicitly enabled.
    """

    if intent is RetrievalIntent.TRANSACTIONAL_RECORD:
        return RetrievalDecision(
            RetrievalRoute.STRUCTURED_SERVICE,
            "Transactional facts must come from an authorized CROWN service.",
        )

    if intent is RetrievalIntent.CANONICAL_GUIDANCE:
        if retrieval_enabled:
            return RetrievalDecision(
                RetrievalRoute.CACHE_THEN_CORPUS,
                "Approved guidance may use cache followed by governed corpus retrieval.",
            )
        return RetrievalDecision(
            RetrievalRoute.ABSTAIN,
            "Governed corpus retrieval is disabled.",
        )

    if intent is RetrievalIntent.AGGREGATE_ANALYSIS:
        if retrieval_enabled and aggregate_retrieval_enabled:
            return RetrievalDecision(
                RetrievalRoute.STRUCTURED_THEN_CORPUS,
                "Approved aggregate facts may be combined with governed explanatory sources.",
            )
        return RetrievalDecision(
            RetrievalRoute.ABSTAIN,
            "Aggregate retrieval is disabled pending separate disclosure controls.",
        )

    return RetrievalDecision(
        RetrievalRoute.ABSTAIN,
        "The request is outside the approved retrieval vocabulary.",
    )


def build_cache_key(
    *,
    tenant_id: str,
    role: str,
    topic: str,
    corpus_version: str,
    policy_version: str,
    question: str,
) -> str:
    """Build a deterministic cache key without retaining raw question text."""

    normalized_question = " ".join(str(question).split()).strip().casefold()
    question_fingerprint = sha256(normalized_question.encode("utf-8")).hexdigest()
    key_material = {
        "corpus_version": str(corpus_version).strip(),
        "policy_version": str(policy_version).strip(),
        "question_fingerprint": question_fingerprint,
        "role": str(role).strip().upper(),
        "tenant_id": str(tenant_id).strip(),
        "topic": str(topic).strip().casefold(),
    }
    digest = sha256(
        json.dumps(key_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"solomon:retrieval:v1:{digest}"


def validate_source_evidence(
    source: SourceEvidence,
    *,
    tenant_id: str,
    role: str,
    as_of: date | None = None,
) -> SourceValidation:
    """Validate provenance, rights, freshness, tenant, and role scope."""

    today = as_of or date.today()
    reasons: list[str] = []

    if not source.source_id.strip():
        reasons.append("missing_source_id")
    if not source.title.strip():
        reasons.append("missing_title")
    if not HEX_64.fullmatch(source.source_digest.strip().lower()):
        reasons.append("invalid_source_digest")
    if not source.source_version.strip():
        reasons.append("missing_source_version")
    if source.provenance_tier not in APPROVED_PROVENANCE_TIERS:
        reasons.append("unapproved_provenance_tier")
    if source.review_status not in APPROVED_REVIEW_STATES:
        reasons.append("unapproved_review_status")
    if source.rights_status not in APPROVED_RIGHTS_STATUSES:
        reasons.append("unapproved_rights_status")
    if source.privacy_classification not in APPROVED_PRIVACY_CLASSES:
        reasons.append("restricted_privacy_classification")

    normalized_scope = source.tenant_scope.strip()
    if normalized_scope != "global" and normalized_scope != str(tenant_id).strip():
        reasons.append("tenant_scope_mismatch")

    normalized_role = str(role).strip().upper()
    if source.role_scope:
        allowed_roles = {item.strip().upper() for item in source.role_scope if item.strip()}
        if normalized_role not in allowed_roles:
            reasons.append("role_scope_mismatch")

    if source.effective_date and source.effective_date > today:
        reasons.append("not_yet_effective")
    if source.expires_on and source.expires_on < today:
        reasons.append("expired")
    if source.reviewed_on is None:
        reasons.append("missing_review_date")

    return SourceValidation(valid=not reasons, reasons=tuple(reasons))


def evaluate_answer_authority(
    sources: Iterable[SourceEvidence],
    *,
    tenant_id: str,
    role: str,
    citations_present: bool,
    restricted_data_detected: bool = False,
    unsupported_claims_detected: bool = False,
    consequential_decision_domain: str = "",
    human_review_required: bool = False,
    human_review_acknowledged: bool = False,
    as_of: date | None = None,
) -> AuthorityGateResult:
    """Fail closed before a retrieved or synthesized answer is released."""

    reasons: list[str] = []
    source_list: Sequence[SourceEvidence] = tuple(sources)

    if restricted_data_detected:
        reasons.append("restricted_data_detected")
    if unsupported_claims_detected:
        reasons.append("unsupported_claims_detected")
    if not citations_present:
        reasons.append("citations_missing")
    if not source_list:
        reasons.append("evidence_missing")

    invalid_sources = []
    for source in source_list:
        validation = validate_source_evidence(
            source,
            tenant_id=tenant_id,
            role=role,
            as_of=as_of,
        )
        if not validation.valid:
            invalid_sources.append(f"{source.source_id}:{','.join(validation.reasons)}")
    if invalid_sources:
        reasons.append("invalid_sources=" + "|".join(invalid_sources))

    normalized_domain = consequential_decision_domain.strip().casefold()
    if normalized_domain in PROHIBITED_DECISION_DOMAINS:
        reasons.append("consequential_decision_requires_human_authority")

    if reasons:
        return AuthorityGateResult(AuthorityDecision.ABSTAIN, tuple(reasons))

    if human_review_required and not human_review_acknowledged:
        return AuthorityGateResult(
            AuthorityDecision.HUMAN_REVIEW,
            ("human_review_required",),
        )

    return AuthorityGateResult(AuthorityDecision.ALLOW, ())
