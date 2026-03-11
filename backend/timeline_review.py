"""
Sample timeline JSON response for review.
This is what director_timeline() endpoint currently returns.
"""

import json
import logging


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SAMPLE_TIMELINE_RESPONSE = {
    "meta": {
        "school_id": "0c0d109f-3752-496b-906b-3b45e16a91fd",
        "year_id": "31cf07c5-38ee-4d0d-aef6-e6adb2704d13",
        "limit": 20,
        "count": 12,
    },
    "timeline": [
        # AID_POSTED_TO_LEDGER events
        {
            "ts": "2026-01-03T14:32:15Z",
            "type": "AID_POSTED_TO_LEDGER",
            "actor": "Director Action",
            "entity": "AidAward",
            "entity_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "amount_cents": 125000,
            "summary": "Aid award posted for John Smith (Smith Family).",
        },
        {
            "ts": "2026-01-03T14:15:42Z",
            "type": "AID_POSTED_TO_LEDGER",
            "actor": "Director Action",
            "entity": "AidAward",
            "entity_id": "b2c3d4e5-f6a7-1234-bcde-f12345678901",
            "amount_cents": 95000,
            "summary": "Aid award posted for Jane Doe (Doe Family).",
        },

        # AID_CONTACT events (noisy — might want to suppress some)
        {
            "ts": "2026-01-03T12:00:00Z",
            "type": "AID_CONTACT",
            "actor": "System",
            "entity": "AidApplication",
            "entity_id": "c3d4e5f6-a7b8-2345-cdef-123456789012",
            "summary": "CONTACT: contacted Johnson Family about financial aid application.",
        },
        {
            "ts": "2026-01-03T11:45:22Z",
            "type": "AID_CONTACT",
            "actor": "System",
            "entity": "AidApplication",
            "entity_id": "d4e5f6a7-b8c9-3456-def1-234567890123",
            "summary": "CONTACT: contacted Brown Family about financial aid application.",
        },
        {
            "ts": "2026-01-03T11:30:15Z",
            "type": "AID_CONTACT",
            "actor": "System",
            "entity": "AidApplication",
            "entity_id": "e5f6a7b8-c9d0-4567-ef12-345678901234",
            "summary": "CONTACT: contacted Garcia Family about financial aid application.",
        },

        # LEDGER_ENTRY events (very noisy — many routine GL entries)
        {
            "ts": "2026-01-03T10:22:08Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "f6a7b8c9-d0e1-5678-f123-456789012345",
            "amount_cents": -5000,
            "summary": "Ledger entry TUITION_CREDIT for Johnson.",
        },
        {
            "ts": "2026-01-03T10:15:33Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "a7b8c9d0-e1f2-6789-0123-567890123456",
            "amount_cents": 8500,
            "summary": "Ledger entry FEES_CHARGE for Brown.",
        },
        {
            "ts": "2026-01-03T10:08:12Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "b8c9d0e1-f2a3-7890-1234-678901234567",
            "amount_cents": -2200,
            "summary": "Ledger entry PAYMENT_RECEIVED for Smith.",
        },
        {
            "ts": "2026-01-03T09:55:44Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "c9d0e1f2-a3b4-8901-2345-789012345678",
            "amount_cents": 0,
            "summary": "Ledger entry GL_ADJUSTMENT for Garcia.",
        },
        {
            "ts": "2026-01-03T09:42:19Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "d0e1f2a3-b4c5-9012-3456-890123456789",
            "amount_cents": 125000,
            "summary": "Ledger entry AID_POSTING for Rodriguez.",
        },

        # More routine ledger noise
        {
            "ts": "2026-01-03T09:30:05Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "e1f2a3b4-c5d6-0123-4567-901234567890",
            "amount_cents": -1500,
            "summary": "Ledger entry SCHOLARSHIP_CREDIT for Martinez.",
        },
    ]
}

# ============================================================================
# FEEDBACK FOR REFINEMENT:
# ============================================================================
#
# ISSUE 1: Timeline Wording
# - "Ledger entry FEES_CHARGE for Brown" → too terse, not "director-friendly"
# - "Ledger entry GL_ADJUSTMENT for Garcia" → zero cents + vague event type
# - "CONTACT: contacted Johnson Family about financial aid application." → repetitive
#
# ISSUE 2: Noisy Rows to Suppress
# - LEDGER_ENTRY events with zero amount_cents (GL_ADJUSTMENT) → noise
# - LEDGER_ENTRY events with small amounts or routine postings → clutter
# - Routine CONTACT events that aren't recent or urgent → bury or hide
# - Could filter by: amount > threshold, type in [AID_POSTED_TO_LEDGER, AID_CONTACT]
#
# ISSUE 3: Storytelling Impact / Reordering
# - Current: reverse chronological (most recent first)
# - Better: Group by impact type:
#     1. Recent AID_POSTED_TO_LEDGER events (director action, high-impact)
#     2. Unresolved AID_CONTACT events (needs follow-up)
#     3. High-value LEDGER_ENTRY events (major tuition changes, payments)
#     4. Routine ledger entries (background, minimal scroll attention)
#
# SUGGESTION: Show sample "tightened" versions below
# ============================================================================

SAMPLE_TIGHTENED = {
    "timeline": [
        # Tightened wording, higher-impact events first
        {
            "ts": "2026-01-03T14:32:15Z",
            "type": "AID_POSTED_TO_LEDGER",
            "actor": "Director Action",
            "entity": "AidAward",
            "entity_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "amount_cents": 125000,
            "summary": "$1,250 aid posted for John Smith",  # Tighter, amount shown
        },
        {
            "ts": "2026-01-03T14:15:42Z",
            "type": "AID_POSTED_TO_LEDGER",
            "actor": "Director Action",
            "entity": "AidAward",
            "entity_id": "b2c3d4e5-f6a7-1234-bcde-f12345678901",
            "amount_cents": 95000,
            "summary": "$950 aid posted for Jane Doe",  # Same pattern
        },

        # High-value ledger entries (payments, significant charges)
        {
            "ts": "2026-01-03T10:08:12Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "b8c9d0e1-f2a3-7890-1234-678901234567",
            "amount_cents": -2200,
            "summary": "Payment received: $22 from Smith",  # Money in = good
        },
        {
            "ts": "2026-01-03T09:42:19Z",
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": "d0e1f2a3-b4c5-9012-3456-890123456789",
            "amount_cents": 125000,
            "summary": "$1,250 aid posted to ledger for Rodriguez",  # Echo of above, but GL side
        },

        # Only include CONTACT events if recent or flagged urgent
        # (omitted routine ones for demo)

        # Suppress: zero-amount entries, routine GL entries, etc.
    ]
}

logger.info(__doc__)
logger.info("\n\nSAMPLE TIMELINE (current):")
logger.info(json.dumps(SAMPLE_TIMELINE_RESPONSE, indent=2))

logger.info("\n\nSAMPLE TIGHTENED (proposal):")
logger.info(json.dumps(SAMPLE_TIGHTENED, indent=2))
