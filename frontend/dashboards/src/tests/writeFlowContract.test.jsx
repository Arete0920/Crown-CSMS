// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const DRAFT_KEY = 'crown_wizard_draft:test-write-wizard';
const draftStore = new Map();
const mockSubmitAdmissionsIntake = vi.fn();
const mockFetchAdmissionsPublicConfig = vi.fn();
const mockSaveDraft = vi.fn();
const mockClearDraft = vi.fn();

const smokeContext = {
  inquiry: {
    campus: 'Heritage Christian Academy',
    startTerm: '2026-2027',
    heardAbout: 'Church referral',
    preferredTourWindow: 'Weekday mornings',
    preferredInterviewMode: 'In person',
  },
  family: {
    guardians: [
      {
        id: 'g-1',
        relationship: 'Mother',
        relationshipOther: '',
        guardianName: 'Jane Doe',
        email: 'jane@example.org',
        phone: '555-010-1111',
        isPrimary: true,
      },
    ],
    churchAffiliation: 'Member at partnering church',
    churchAffiliationOther: '',
  },
  students: [
    {
      id: 's-1',
      firstName: 'John',
      lastName: 'Doe',
      gradeApplyingFor: '5',
      currentSchool: 'Public school',
      currentSchoolOther: '',
      interestsAndActivities: ['Reading'],
      supportNeeds: [],
    },
  ],
  mission: {
    covenantPartnership: true,
    discipleshipCommitment: true,
    serviceMindset: true,
    churchAttendance: "Weekly",
    commitmentToChrist: "Parent or guardian professes faith in Christ",
    spiritualLifeComments: "Family seeks Christ-centered growth.",
    alignmentFocus: ['Spiritual formation'],
    comments: 'Aligned',
    studentPortraitRatings: {
      "s-1": {
        christ_centered_identity: 4,
        biblical_worldview: 4,
        servant_leadership: 3,
        academic_readiness: 4,
        community_impact: 3,
      },
    },
  },
  documents: {
    transcriptReady: true,
    recommendationsReady: true,
    pastorReferenceReady: true,
    immunizationReady: true,
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

vi.mock('../hooks/useWizardDraft', () => ({
  useWizardDraft: () => ({
    value: smokeContext,
    saveDraft: mockSaveDraft,
    clearDraft: mockClearDraft,
    loaded: true,
    lastSavedAt: null,
  }),
}));

vi.mock('../api/admissions', () => ({
  fetchAdmissionsPublicConfig: (...args) => mockFetchAdmissionsPublicConfig(...args),
  submitAdmissionsIntake: (...args) => mockSubmitAdmissionsIntake(...args),
}));

function saveDraft(value) {
  draftStore.set(
    DRAFT_KEY,
    JSON.stringify({ __draftVersion: 2, value, savedAt: new Date().toISOString() }),
  );
}

function clearDraft() {
  draftStore.delete(DRAFT_KEY);
}

function readDraft() {
  return draftStore.get(DRAFT_KEY) || null;
}

function createSubmitFlow(request, onSuccess = () => {}) {
  let loading = false;
  let error = null;

  const submit = async (value) => {
    loading = true;
    error = null;

    try {
      await request(value);
      clearDraft();
      onSuccess();
      return { ok: true };
    } catch (err) {
      saveDraft(value);
      error = err;
      return { ok: false, error: err };
    } finally {
      loading = false;
    }
  };

  return {
    submit,
    get loading() {
      return loading;
    },
    get error() {
      return error;
    },
  };
}

const mockCreate = vi.fn();

describe('write flow contract', () => {
  afterEach(() => {
    cleanup();
    draftStore.clear();
    vi.unstubAllGlobals();
  });

  beforeEach(() => {
    draftStore.clear();
    mockCreate.mockReset();
    mockSubmitAdmissionsIntake.mockReset();
    mockFetchAdmissionsPublicConfig.mockReset();
    mockSaveDraft.mockReset();
    mockClearDraft.mockReset();

    mockFetchAdmissionsPublicConfig.mockResolvedValue({
      application_fee: {
        required: true,
        amount: 85,
        currency: 'USD',
      },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
        }),
      ),
    );
  });

  it('clears draft only on successful submit', async () => {
    const onSuccess = vi.fn();
    const payload = { first_name: 'John' };

    mockCreate.mockResolvedValueOnce({ id: 123 });
    saveDraft(payload);

    const flow = createSubmitFlow(mockCreate, onSuccess);

    expect(readDraft()).toContain('John');

    const result = await flow.submit(payload);

    expect(result.ok).toBe(true);
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(readDraft()).toBeNull();
  });

  it('preserves draft and shows field errors on failed submit', async () => {
    const onSuccess = vi.fn();
    const payload = { first_name: 'Bad Value' };

    mockCreate.mockRejectedValueOnce({
      message: 'Validation failed.',
      status: 400,
      fieldErrors: {
        first_name: 'This field is required.',
      },
    });

    saveDraft(payload);

    const flow = createSubmitFlow(mockCreate, onSuccess);

    const result = await flow.submit(payload);

    expect(result.ok).toBe(false);
    expect(result.error.message).toBe('Validation failed.');
    expect(result.error.fieldErrors.first_name).toBe('This field is required.');
    expect(flow.error.message).toBe('Validation failed.');
    expect(onSuccess).not.toHaveBeenCalled();
    expect(readDraft()).toContain('Bad Value');
  });

  it('locks the submit button during request', async () => {
    let resolver;

    mockCreate.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolver = resolve;
        }),
    );

    const flow = createSubmitFlow(mockCreate, () => {});
    const promise = flow.submit({ first_name: 'Jane' });

    expect(flow.loading).toBe(true);

    resolver({ id: 999 });

    await promise;

    expect(flow.loading).toBe(false);
  });

  it('renders admissions wizard and surfaces submit failure', async () => {
    mockSubmitAdmissionsIntake.mockRejectedValueOnce({
      message: 'Validation failed from smoke test.',
      correlationId: 'smoke-correlation-id',
    });

    const { default: ProspectiveFamilyAdmissionsWizard } = await import('../pages/ProspectiveFamilyAdmissionsWizard.jsx');
    render(<ProspectiveFamilyAdmissionsWizard />);

    expect(screen.getByText('Current journey stage')).toBeTruthy();
    expect(screen.getByText(/your next action:/i)).toBeTruthy();

    for (let i = 0; i < 6; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    }

    fireEvent.click(screen.getByLabelText(/we are not applying for financial aid\./i));
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /submit application/i }));

    const submitButton = await screen.findByRole('button', { name: /confirm and submit/i });
    await waitFor(() => {
      expect(submitButton.disabled).toBe(false);
    });

    fireEvent.click(submitButton);

    expect(await screen.findByText('Validation failed from smoke test.')).toBeTruthy();
    expect(screen.getByText(/support reference:/i)).toBeTruthy();
    expect(mockSubmitAdmissionsIntake).toHaveBeenCalledTimes(1);
  }, 20000);
});
