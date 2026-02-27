"""
Tests for admissions.services.move_stage().

Uses a lightweight stub (_FakeApp) — no DB, no Django fixtures — for pure FSM
assertions.  Only the passthrough/delegation tests care about call args; they
still don't touch the database.

Run:
    .venv/Scripts/python.exe -m pytest backend/admissions/tests.py -q --tb=short
"""
from django.test import TestCase

from admissions.models import AdmissionsApplication
from admissions.services import (
    ALLOWED_TRANSITIONS,
    InvalidStageTransition,
    move_stage,
)

A = AdmissionsApplication  # short alias for status constants


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeApp:
    """
    Minimal stub satisfying move_stage()'s duck-type requirements.
    Captures set_status() calls without touching the database.
    """

    def __init__(self, status: str):
        self.status = status
        self._calls: list[tuple] = []

    def set_status(self, new_status: str, actor_user=None, details=None):
        self._calls.append((new_status, actor_user, details))
        self.status = new_status  # mirror real model behaviour


# ---------------------------------------------------------------------------
# Happy-path: allowed transitions
# ---------------------------------------------------------------------------

class TestMoveStageValidTransitions(TestCase):
    """move_stage() succeeds and calls set_status() exactly once per allowed edge."""

    def _assert_ok(self, from_status: str, to_status: str):
        app = _FakeApp(from_status)
        result = move_stage(app, to_status)

        self.assertIs(result, app, "move_stage() must return the record")
        self.assertEqual(app.status, to_status)
        self.assertEqual(len(app._calls), 1, "set_status() must be called exactly once")
        self.assertEqual(app._calls[0][0], to_status)

    def test_draft_to_submitted(self):
        self._assert_ok(A.STATUS_DRAFT, A.STATUS_SUBMITTED)

    def test_draft_to_withdrawn(self):
        self._assert_ok(A.STATUS_DRAFT, A.STATUS_WITHDRAWN)

    def test_submitted_to_under_review(self):
        self._assert_ok(A.STATUS_SUBMITTED, A.STATUS_UNDER_REVIEW)

    def test_submitted_to_needs_info(self):
        self._assert_ok(A.STATUS_SUBMITTED, A.STATUS_NEEDS_INFO)

    def test_submitted_to_withdrawn(self):
        self._assert_ok(A.STATUS_SUBMITTED, A.STATUS_WITHDRAWN)

    def test_under_review_to_accepted(self):
        self._assert_ok(A.STATUS_UNDER_REVIEW, A.STATUS_ACCEPTED)

    def test_under_review_to_denied(self):
        self._assert_ok(A.STATUS_UNDER_REVIEW, A.STATUS_DENIED)

    def test_under_review_to_waitlisted(self):
        self._assert_ok(A.STATUS_UNDER_REVIEW, A.STATUS_WAITLISTED)

    def test_under_review_to_needs_info(self):
        self._assert_ok(A.STATUS_UNDER_REVIEW, A.STATUS_NEEDS_INFO)

    def test_under_review_to_withdrawn(self):
        self._assert_ok(A.STATUS_UNDER_REVIEW, A.STATUS_WITHDRAWN)

    def test_needs_info_to_submitted(self):
        self._assert_ok(A.STATUS_NEEDS_INFO, A.STATUS_SUBMITTED)

    def test_needs_info_to_withdrawn(self):
        self._assert_ok(A.STATUS_NEEDS_INFO, A.STATUS_WITHDRAWN)

    def test_accepted_to_enrolled(self):
        self._assert_ok(A.STATUS_ACCEPTED, A.STATUS_ENROLLED)

    def test_accepted_to_withdrawn(self):
        self._assert_ok(A.STATUS_ACCEPTED, A.STATUS_WITHDRAWN)

    def test_waitlisted_to_accepted(self):
        self._assert_ok(A.STATUS_WAITLISTED, A.STATUS_ACCEPTED)

    def test_waitlisted_to_denied(self):
        self._assert_ok(A.STATUS_WAITLISTED, A.STATUS_DENIED)

    def test_waitlisted_to_withdrawn(self):
        self._assert_ok(A.STATUS_WAITLISTED, A.STATUS_WITHDRAWN)


# ---------------------------------------------------------------------------
# Invalid transitions: exception raised, record NOT mutated
# ---------------------------------------------------------------------------

class TestMoveStageInvalidTransitions(TestCase):
    """move_stage() raises InvalidStageTransition; record.status is unchanged."""

    def _assert_blocked(self, from_status: str, to_status: str):
        app = _FakeApp(from_status)
        with self.assertRaises(InvalidStageTransition):
            move_stage(app, to_status)
        # Guard: no mutation must have occurred
        self.assertEqual(app.status, from_status, "status must not change on failure")
        self.assertEqual(app._calls, [], "set_status() must not be called on failure")

    def test_enrolled_to_submitted_blocked(self):
        self._assert_blocked(A.STATUS_ENROLLED, A.STATUS_SUBMITTED)

    def test_enrolled_to_draft_blocked(self):
        self._assert_blocked(A.STATUS_ENROLLED, A.STATUS_DRAFT)

    def test_enrolled_to_accepted_blocked(self):
        self._assert_blocked(A.STATUS_ENROLLED, A.STATUS_ACCEPTED)

    def test_denied_to_accepted_blocked(self):
        self._assert_blocked(A.STATUS_DENIED, A.STATUS_ACCEPTED)

    def test_denied_to_under_review_blocked(self):
        self._assert_blocked(A.STATUS_DENIED, A.STATUS_UNDER_REVIEW)

    def test_withdrawn_to_under_review_blocked(self):
        self._assert_blocked(A.STATUS_WITHDRAWN, A.STATUS_UNDER_REVIEW)

    def test_withdrawn_to_draft_blocked(self):
        self._assert_blocked(A.STATUS_WITHDRAWN, A.STATUS_DRAFT)

    def test_draft_to_enrolled_blocked(self):
        self._assert_blocked(A.STATUS_DRAFT, A.STATUS_ENROLLED)

    def test_draft_to_accepted_blocked(self):
        self._assert_blocked(A.STATUS_DRAFT, A.STATUS_ACCEPTED)

    def test_needs_info_to_accepted_blocked(self):
        self._assert_blocked(A.STATUS_NEEDS_INFO, A.STATUS_ACCEPTED)

    def test_needs_info_to_enrolled_blocked(self):
        self._assert_blocked(A.STATUS_NEEDS_INFO, A.STATUS_ENROLLED)


# ---------------------------------------------------------------------------
# Terminal state contract: no outbound edges in ALLOWED_TRANSITIONS
# ---------------------------------------------------------------------------

class TestTerminalStates(TestCase):
    """
    DENIED, ENROLLED, WITHDRAWN must be absent from ALLOWED_TRANSITIONS keys.
    Their absence is what makes them terminal — not a hardcoded special case.
    """

    TERMINAL = {A.STATUS_DENIED, A.STATUS_ENROLLED, A.STATUS_WITHDRAWN}

    def test_terminal_states_absent_from_transition_graph(self):
        for terminal in self.TERMINAL:
            with self.subTest(terminal=terminal):
                self.assertNotIn(
                    terminal,
                    ALLOWED_TRANSITIONS,
                    msg=f"{terminal!r} must have no outbound edges (terminal status)",
                )

    def test_any_move_from_terminal_raises(self):
        """Exhaustive: every terminal × every non-self target raises."""
        all_statuses = {s for s, _ in A.STATUS_CHOICES}
        for terminal in self.TERMINAL:
            for target in all_statuses - {terminal}:
                with self.subTest(terminal=terminal, target=target):
                    app = _FakeApp(terminal)
                    with self.assertRaises(InvalidStageTransition):
                        move_stage(app, target)
                    self.assertEqual(app._calls, [])


# ---------------------------------------------------------------------------
# Error message quality
# ---------------------------------------------------------------------------

class TestInvalidStageTransitionMessage(TestCase):
    """Exception message must name both the source and target status."""

    def test_message_contains_from_status(self):
        app = _FakeApp(A.STATUS_ENROLLED)
        with self.assertRaises(InvalidStageTransition) as ctx:
            move_stage(app, A.STATUS_DRAFT)
        self.assertIn(A.STATUS_ENROLLED, str(ctx.exception))

    def test_message_contains_to_status(self):
        app = _FakeApp(A.STATUS_ENROLLED)
        with self.assertRaises(InvalidStageTransition) as ctx:
            move_stage(app, A.STATUS_DRAFT)
        self.assertIn(A.STATUS_DRAFT, str(ctx.exception))

    def test_message_on_terminal_status_mentions_none(self):
        """Terminal statuses should report 'none' (no outbound) in the message."""
        app = _FakeApp(A.STATUS_DENIED)
        with self.assertRaises(InvalidStageTransition) as ctx:
            move_stage(app, A.STATUS_SUBMITTED)
        self.assertIn("none", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# Actor + details passthrough
# ---------------------------------------------------------------------------

class TestMoveStageActorPassthrough(TestCase):
    """actor_user and details are forwarded verbatim to set_status()."""

    def test_actor_user_forwarded(self):
        app = _FakeApp(A.STATUS_DRAFT)
        fake_user = object()
        move_stage(app, A.STATUS_SUBMITTED, actor_user=fake_user, details={"note": "ci"})
        new_status, actor, details = app._calls[0]
        self.assertEqual(new_status, A.STATUS_SUBMITTED)
        self.assertIs(actor, fake_user)
        self.assertEqual(details, {"note": "ci"})

    def test_details_defaults_to_empty_dict(self):
        app = _FakeApp(A.STATUS_DRAFT)
        move_stage(app, A.STATUS_SUBMITTED)
        _, _, details = app._calls[0]
        self.assertEqual(details, {})

    def test_none_actor_is_valid(self):
        app = _FakeApp(A.STATUS_SUBMITTED)
        move_stage(app, A.STATUS_UNDER_REVIEW, actor_user=None)
        _, actor, _ = app._calls[0]
        self.assertIsNone(actor)
