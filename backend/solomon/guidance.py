"""Structured Solomon guidance. No records, user text, or network transport.

The external payload builder is deliberately narrower than a redaction filter:
only maintained, repository-owned instructions can cross this boundary.
"""
from __future__ import annotations

from hashlib import sha256
import json
from types import MappingProxyType

POLICY_VERSION = "solomon-guidance-v1"
GUIDANCE = MappingProxyType({
    "onboarding": (
        "Plan CROWN implementation",
        "Confirm the school's implementation owner, assigned roles, training schedule, "
        "and acceptance checklist. Review configuration with authorized staff before go-live.",
    ),
    "interpretation": (
        "Understand decision-support outputs",
        "Review the documented assumptions, source freshness, and limitations of a forecast. "
        "Treat indicators as reasons for human investigation. Leadership remains responsible "
        "for decisions; do not infer an individual student's circumstances from an indicator.",
    ),
    "governance": (
        "Review operating governance",
        "Identify the accountable school leader, review access permissions and retention "
        "rules, and document the human approval required before changing school policy.",
    ),
    "strategy": (
        "Request school-specific advisory support",
        "Bring school-specific strategy, tuition planning, financial aid policy, and "
        "consequential decisions to school leadership and Arete Advisory Group. "
        "Solomon provides general guidance and does not make these decisions.",
    ),
})


class GuidanceInputError(ValueError):
    """A request falls outside the closed guidance vocabulary."""


def validate_selection(data):
    # Exact keys/types: no IDs, records, arbitrary instructions, attachments or metrics.
    if type(data) is not dict or set(data) != {"topic", "human_review_acknowledged"}:
        raise GuidanceInputError("Select a supported guidance topic and acknowledge human review.")
    topic = data["topic"]
    if type(topic) is not str or topic not in GUIDANCE:
        raise GuidanceInputError("Unsupported guidance topic.")
    if data["human_review_acknowledged"] is not True:
        raise GuidanceInputError("Human review acknowledgement is required.")
    return topic


def build_external_payload(data):
    """Prepare only curated generic text, never transmit it.

    Aggregates are intentionally rejected too: safe cohort thresholds, repeated-query
    disclosure and jurisdiction-specific review are not established yet.
    """
    topic = validate_selection(data)
    title, guidance = GUIDANCE[topic]
    if topic == "strategy":
        raise GuidanceInputError("School-specific strategy requires human advisory support.")
    return {
        "policy_version": POLICY_VERSION,
        "task": "Explain this general CROWN guidance for an adult staff member. "
                "Do not make decisions or invent facts. Human review is required.",
        "topic": topic,
        "source": {"title": title, "guidance": guidance},
    }


def local_guidance(data):
    topic = validate_selection(data)
    title, guidance = GUIDANCE[topic]
    provenance = sha256(json.dumps(
        {"policy": POLICY_VERSION, "topic": topic, "guidance": guidance},
        sort_keys=True,
    ).encode("utf-8")).hexdigest()
    return {
        "topic": topic,
        "title": title,
        "guidance": guidance,
        "mode": "curated_guidance",
        "generated_by_ai": False,
        "human_review_required": True,
        "advisory_handoff": topic == "strategy",
        "external_ai_status": "blocked_pending_provider_and_release_review",
        "policy_version": POLICY_VERSION,
        "source": "CROWN Solomon guidance catalog",
        "source_digest": provenance,
    }
