// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ParentLifecycleStatusCenterPage from "../pages/ParentLifecycleStatusCenterPage.jsx";
import { loadParentJourneyOverview } from "../features/parentJourney/parentJourneyState.js";

vi.mock("../features/parentJourney/parentJourneyState.js", () => ({
  loadParentJourneyOverview: vi.fn(),
}));

describe("parent status center scaffold", () => {
  it("renders the five parent readiness sections", async () => {
    loadParentJourneyOverview.mockResolvedValueOnce({
      children_count: 2,
      missing_assignments_total: 1,
      upcoming_assignments_total: 3,
      household: {
        name: "Heritage Household",
        balance_cents: 12500,
      },
      admissions_continuity: {
        summary: {
          total: 1,
          accepted_pending_contract: 1,
          contract_complete: 0,
          deposit_complete: 0,
        },
        applications: [
          {
            application_id: "app-1",
            application_status: "submitted",
            lifecycle_stage: "accepted",
            parent_status: "Accepted pending contract",
            next_action: "Sign contract and submit deposit.",
            submitted_at: "2026-05-30T12:00:00Z",
            checklist_summary: {
              missing_count: 2,
              required_total: 8,
            },
            financial_aid_status: "in_review",
            aid_award_count: 1,
            aid_contract_sync_status: "pending",
            contract_status: "pending",
            deposit_status: "pending",
            payment_precheck: {
              status: "pending",
            },
            classroom_readiness_status: "in_progress",
            applicant_to_student_status: "pending",
            parent_portal_activation_status: "in_progress",
          },
        ],
      },
    });

    render(<ParentLifecycleStatusCenterPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /parent lifecycle status/i })).toBeTruthy();
    });

    expect(screen.getByText("Admissions readiness")).toBeTruthy();
    expect(screen.getByText("Financial aid readiness")).toBeTruthy();
    expect(screen.getByText("Contract & deposit readiness")).toBeTruthy();
    expect(screen.getByText("Billing readiness")).toBeTruthy();
    expect(screen.getByText("Classroom readiness")).toBeTruthy();
  });
});
