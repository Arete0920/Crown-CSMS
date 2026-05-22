// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const smokeContext = {
  inquiry: {
    campus: "Heritage Christian Academy",
    startTerm: "2026-2027",
    heardAbout: "Church referral",
    preferredTourWindow: "Weekday mornings",
    preferredInterviewMode: "In person",
  },
  family: {
    guardians: [
      {
        id: "g-1",
        relationship: "Mother",
        relationshipOther: "",
        guardianName: "Jane Doe",
        email: "jane@example.org",
        phone: "555-010-1111",
        isPrimary: true,
      },
    ],
    churchAffiliation: "Member at partnering church",
    churchAffiliationOther: "",
  },
  students: [
    {
      id: "s-1",
      firstName: "John",
      lastName: "Doe",
      gradeApplyingFor: "5",
      currentSchool: "Public school",
      currentSchoolOther: "",
      strengths: "Reading",
      supportNeeds: "",
    },
  ],
  mission: {
    covenantPartnership: true,
    discipleshipCommitment: true,
    serviceMindset: true,
    comments: "Aligned",
  },
  documents: {
    transcriptReady: true,
    recommendationsReady: true,
    pastorReferenceReady: false,
    immunizationReady: false,
  },
  attestations: {
    informationAccurate: true,
    missionPartnershipUnderstood: true,
    communicationOptIn: true,
  },
  applicationFee: {
    policyAccepted: true,
    waiverRequested: false,
  },
  submitted: false,
};

const mockSubmitAdmissionsIntake = vi.fn();
const mockFetchAdmissionsPublicConfig = vi.fn();
const mockSaveDraft = vi.fn();
const mockClearDraft = vi.fn();

vi.mock("../hooks/useWizardDraft", () => ({
  useWizardDraft: () => ({
    value: smokeContext,
    saveDraft: mockSaveDraft,
    clearDraft: mockClearDraft,
    loaded: true,
    lastSavedAt: null,
  }),
}));

vi.mock("../api/admissions", () => ({
  fetchAdmissionsPublicConfig: (...args) => mockFetchAdmissionsPublicConfig(...args),
  submitAdmissionsIntake: (...args) => mockSubmitAdmissionsIntake(...args),
}));

beforeEach(() => {
  mockSubmitAdmissionsIntake.mockReset();
  mockFetchAdmissionsPublicConfig.mockReset();
  mockSaveDraft.mockReset();
  mockClearDraft.mockReset();

  mockFetchAdmissionsPublicConfig.mockResolvedValue({
    application_fee: {
      required: true,
      amount: 85,
      currency: "USD",
    },
  });

  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
      }),
    ),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("write flow UI integration smoke", () => {
  it("renders admissions wizard and surfaces submit failure", async () => {
    mockSubmitAdmissionsIntake.mockRejectedValueOnce({
      message: "Validation failed from smoke test.",
      correlationId: "smoke-correlation-id",
    });

    const { default: ProspectiveFamilyAdmissionsWizard } = await import("../pages/ProspectiveFamilyAdmissionsWizard.jsx");
    render(<ProspectiveFamilyAdmissionsWizard />);

    for (let i = 0; i < 6; i += 1) {
      fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    }

    fireEvent.click(screen.getByRole("button", { name: /submit application/i }));

    const submitButton = await screen.findByRole("button", { name: /confirm and submit/i });
    await waitFor(() => {
      expect(submitButton.disabled).toBe(false);
    });

    fireEvent.click(submitButton);

    expect(await screen.findByText("Validation failed from smoke test.")).toBeTruthy();
    expect(screen.getByText(/support reference:/i)).toBeTruthy();
    expect(mockSubmitAdmissionsIntake).toHaveBeenCalledTimes(1);
  });
});
