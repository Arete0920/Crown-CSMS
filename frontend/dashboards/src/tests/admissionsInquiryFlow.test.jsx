// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import AdmissionsInquiryPage from '../pages/AdmissionsInquiryPage.jsx';
import AdmissionsInquiryQueue from '../pages/AdmissionsInquiryQueue.jsx';
import ProspectiveFamilyAdmissionsWizard from '../pages/ProspectiveFamilyAdmissionsWizard.jsx';
import MarketingDashboard from '../pages/MarketingDashboard.jsx';
import { clearAdmissionsInquiry, clearPendingAdmissionsInquiry, inquiryEntryPath, loadAdmissionsInquiry } from '../lib/admissionsInquiryState.js';

const api = vi.hoisted(() => ({ submit: vi.fn(), start: vi.fn(), list: vi.fn(), detail: vi.fn(), update: vi.fn(), application: vi.fn(), dashboard: vi.fn() }));
vi.mock('../api/admissionsInquiries.js', async (original) => ({ ...(await original()), submitAdmissionsInquiry: api.submit, startInquiryApplication: api.start, fetchAdmissionsInquiries: api.list, fetchAdmissionsInquiry: api.detail, updateAdmissionsInquiry: api.update }));
vi.mock('../api/admissions.js', () => ({ fetchAdmissionsPublicConfig: async () => ({ application_fee: { required: false, amount: 0, currency: 'USD' } }), submitAdmissionsIntake: api.application }));
vi.mock('../components/crown/CrownLayout.jsx', () => ({ default: ({ title, children }) => <main><h1>{title}</h1>{children}</main> }));
vi.mock('../hooks/useDashboardData.js', () => ({ default: api.dashboard }));
vi.mock('../components/crown-dashboard/CrownDashboardTemplate.jsx', () => ({ default: ({ config }) => <pre data-testid="marketing-modules">{JSON.stringify(config.commandModules)}</pre> }));

const SCHOOL = 'aa000000-0000-4000-8000-000000000001';
const INQUIRY = 'bb000000-0000-4000-8000-000000000001';
const TOKEN = 'synthetic-test-continuation';
const receipt = { inquiry_id: INQUIRY, continuation_token: TOKEN, school_id: SCHOOL, school_name: 'River School', stage: 'inquiry', next_step: 'Admissions will contact you about your visit.' };

function renderJourney() {
  return render(<MemoryRouter initialEntries={[globalThis.location.pathname + globalThis.location.search]}><Routes>
    <Route path="/admissions/inquire" element={<AdmissionsInquiryPage />} />
    <Route path="/admissions/apply" element={<ProspectiveFamilyAdmissionsWizard />} />
  </Routes></MemoryRouter>);
}

function fillInquiry() {
  fireEvent.change(screen.getByLabelText(/Parent or guardian name/), { target: { value: 'Jordan Reed' } });
  fireEvent.change(screen.getByLabelText(/Email address/), { target: { value: 'jordan@example.org' } });
  fireEvent.change(screen.getByLabelText(/Grade of interest/), { target: { value: '6' } });
  fireEvent.change(screen.getByLabelText(/School year of interest/), { target: { value: '2029-2030' } });
  fireEvent.change(screen.getByLabelText(/How did you hear/), { target: { value: 'community_event' } });
  fireEvent.click(screen.getByLabelText(/I allow this school/));
}

beforeEach(() => {
  cleanup();
  localStorage.clear(); sessionStorage.clear(); clearAdmissionsInquiry(); clearPendingAdmissionsInquiry();
  Object.values(api).forEach((mock) => mock.mockReset());
  api.submit.mockResolvedValue(receipt);
  api.start.mockResolvedValue({ inquiry_id: INQUIRY, school_id: SCHOOL, school_name: 'River School', stage: 'application_started' });
  globalThis.history.replaceState({}, '', `/admissions/inquire?school_id=${SCHOOL}&campus=River%20School&request_type=tour&utm_source=church&utm_campaign=open-house&private_parameter=do-not-save`);
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) })));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); clearAdmissionsInquiry(); clearPendingAdmissionsInquiry(); });

describe('prospective-family inquiry capture', () => {
  it('binds the real transport to the intended school and sends continuation only in the body', async () => {
    expect(inquiryEntryPath()).toContain('request_type=tour');
    expect(inquiryEntryPath()).not.toContain('private_parameter');
    const transport = await vi.importActual('../api/admissionsInquiries.js');
    sessionStorage.setItem('crown.school.id', 'different-remembered-school');
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(receipt), { status: 201, headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetchMock);
    await transport.submitAdmissionsInquiry({ school_id: SCHOOL, campus: 'River School' }, 'stable-test-key');
    expect(fetchMock.mock.calls[0][1].headers.get('X-School-Id')).toBe(SCHOOL);
    expect(fetchMock.mock.calls[0][1].headers.get('Idempotency-Key')).toBe('stable-test-key');
    await transport.startInquiryApplication(receipt);
    expect(fetchMock.mock.calls[1][0]).toContain(`/inquiries/${INQUIRY}/start/`);
    expect(fetchMock.mock.calls[1][0]).not.toContain(TOKEN);
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toMatchObject({ school_id: SCHOOL, continuation_token: TOKEN });
    await transport.submitAdmissionsInquiry({ school_id: '', campus: 'River School' }, 'another-test-key');
    expect(fetchMock.mock.calls[2][1].headers.get('X-School-Id')).toBe('');
  });

  it('persists a consented inquiry before an application and keeps source/UTM separate', async () => {
    renderJourney();
    expect(screen.getByLabelText(/Send me admissions follow-up reminders/).checked).toBe(false);
    fireEvent.submit(screen.getByRole('form', { name: 'Admissions inquiry' }));
    expect(api.submit).not.toHaveBeenCalled();
    fillInquiry();
    expect(screen.getByLabelText('Request a campus visit').checked).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'Send my request' }));
    await screen.findByRole('region', { name: 'Inquiry receipt' });
    expect(api.application).not.toHaveBeenCalled();
    expect(api.submit.mock.calls[0][0]).toMatchObject({ school_id: SCHOOL, parent_name: 'Jordan Reed', grade_interest: '6', entry_year: '2029-2030', request_type: 'tour', source: 'community_event', response_consent: true, follow_up_consent: false, utm: { utm_source: 'church', utm_campaign: 'open-house' } });
    expect(api.submit.mock.calls[0][0].utm.landing_page).not.toContain('?');
    expect(JSON.stringify(api.submit.mock.calls[0][0])).not.toContain('do-not-save');
    expect(loadAdmissionsInquiry(SCHOOL).inquiry_id).toBe(INQUIRY);
    expect(screen.getByText(/A visit date is confirmed only after/)).toBeTruthy();
    for (const link of screen.getAllByRole('link')) expect(link.getAttribute('href')).not.toContain(TOKEN);
  });

  it.each(['phone', 'sms'])('validates text-message addressing while retaining %s contact behavior', async (method) => {
    renderJourney(); fillInquiry();
    fireEvent.change(screen.getByLabelText('Preferred contact method'), { target: { value: 'sms' } });
    fireEvent.change(screen.getByLabelText(/Phone number/), { target: { value: '(302) 555-0100' } });
    fireEvent.submit(screen.getByRole('form', { name: 'Admissions inquiry' }));
    expect(screen.getByRole('alert').textContent).toContain('For SMS, use a country code');
    expect(api.submit).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText('Preferred contact method'), { target: { value: method } });
    if (method === 'sms') fireEvent.change(screen.getByLabelText(/Phone number/), { target: { value: '+13025550100' } });
    fireEvent.submit(screen.getByRole('form', { name: 'Admissions inquiry' }));
    await screen.findByRole('region', { name: 'Inquiry receipt' });
    expect(api.submit.mock.calls[0][0]).toMatchObject({ contact_preference: method, phone: method === 'sms' ? '+13025550100' : '(302) 555-0100' });
  });

  it('retains the same retry identity after an uncertain response and page remount', async () => {
    api.submit.mockRejectedValueOnce({ message: 'Network response unavailable. Please retry.' });
    const view = renderJourney(); fillInquiry();
    fireEvent.click(screen.getByRole('button', { name: 'Send my request' }));
    await screen.findByText('Network response unavailable. Please retry.');
    const firstKey = api.submit.mock.calls[0][1];
    expect(loadAdmissionsInquiry(SCHOOL)).toBeNull();
    view.unmount(); renderJourney();
    expect(screen.getByLabelText(/Parent or guardian name/).value).toBe('Jordan Reed');
    fireEvent.click(screen.getByRole('button', { name: 'Send my request' }));
    await screen.findByRole('region', { name: 'Inquiry receipt' });
    expect(api.submit.mock.calls[1][1]).toBe(firstKey);
    expect(api.application).not.toHaveBeenCalled();
  });

  it('resumes the saved inquiry into the real wizard with school/year/source and contacts', async () => {
    const view = renderJourney(); fillInquiry();
    fireEvent.change(screen.getByLabelText(/Grade of interest/), { target: { value: 'Pre-K' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send my request' }));
    await screen.findByRole('region', { name: 'Inquiry receipt' });
    view.unmount(); renderJourney();
    expect(screen.getByRole('region', { name: 'Inquiry receipt' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Continue to application' }));
    await screen.findByText(/Your saved inquiry and original referral stay linked/);
    expect(api.start).toHaveBeenCalledWith(expect.objectContaining({ inquiry_id: INQUIRY, continuation_token: TOKEN, school_id: SCHOOL }));
    fireEvent.click(screen.getByRole('button', { name: /Continue/ }));
    expect(screen.getByLabelText('Campus *').value).toBe('River School');
    expect(screen.getByLabelText('Start Term *').value).toBe('2029-2030');
    expect(screen.getByLabelText(/How did you hear/).value).toBe('community_event');
    fireEvent.click(screen.getByRole('button', { name: /Continue/ }));
    expect(screen.getByDisplayValue('Jordan Reed')).toBeTruthy();
    expect(screen.getByDisplayValue('jordan@example.org')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Phone *'), { target: { value: '(302) 555-0100' } });
    fireEvent.change(screen.getByLabelText('Relationship *'), { target: { value: 'Guardian' } });
    fireEvent.click(screen.getByRole('button', { name: /Continue/ }));
    expect(screen.getByLabelText('Grade Applying For *').value).toBe('Pre-K');
    expect(localStorage.getItem(`crown_wizard_draft:admissions-apply:${SCHOOL}:${INQUIRY}`)).not.toContain(TOKEN);
  });

  it('keeps a scoped, expiring continuation across a new tab without persisting contact details', async () => {
    renderJourney(); fillInquiry();
    fireEvent.click(screen.getByRole('button', { name: 'Send my request' }));
    await screen.findByRole('region', { name: 'Inquiry receipt' });
    const persisted = localStorage.getItem(`crown_admissions_inquiry_receipt:${SCHOOL}`);
    expect(persisted).not.toContain('Jordan Reed');
    expect(persisted).not.toContain('jordan@example.org');
    sessionStorage.clear();
    vi.resetModules();
    const freshTab = await import('../lib/admissionsInquiryState.js');
    expect(freshTab.loadAdmissionsInquiry(SCHOOL)).toMatchObject({ inquiry_id: INQUIRY, continuation_token: TOKEN });
    expect(freshTab.loadAdmissionsInquiry('another-school')).toBeNull();
    localStorage.setItem(`crown_admissions_inquiry_receipt:${SCHOOL}`, JSON.stringify({ ...JSON.parse(persisted), expires_at: '2020-01-01T00:00:00Z' }));
    expect(freshTab.loadAdmissionsInquiry(SCHOOL)).toBeNull();
  });
});

describe('staff inquiry follow-up queue', () => {
  it.each([false, true, undefined])('reports the collection switch only after loading an empty queue (%s)', async (enabled) => {
    api.list.mockResolvedValue({ results: [], count: 0, owners: [], can_edit: false, ...(enabled === undefined ? {} : { notifications_enabled: enabled }) });
    render(<AdmissionsInquiryQueue />);
    expect(screen.getByText('Loading school inquiries…')).toBeTruthy();
    expect(screen.queryByText(/Automatic inquiry messages are off\./)).toBeNull();
    await screen.findByText('No inquiries match these filters.');
    const note = screen.queryByText(/Automatic inquiry messages are off\./);
    if (enabled === false) expect(note).toBeTruthy();
    else expect(note).toBeNull();
    expect(screen.queryByRole('form', { name: 'Update inquiry follow-up' })).toBeNull();
    expect(api.update).not.toHaveBeenCalled();
  });

  it('retains the off notice for a read-only filtered-empty queue and clears it on a failed refresh', async () => {
    api.list.mockResolvedValue({ results: [], count: 0, owners: [], can_edit: false, notifications_enabled: false });
    render(<AdmissionsInquiryQueue />);
    await screen.findByText('No inquiries match these filters.');
    fireEvent.click(screen.getByLabelText('Unassigned'));
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({ stage: '', unassigned: 1, overdue: '' }));
    await screen.findByText('No inquiries match these filters.');
    fireEvent.click(screen.getByLabelText('Follow-up due'));
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({ stage: '', unassigned: 1, overdue: 1 }));
    await screen.findByText('No inquiries match these filters.');
    expect(screen.getAllByText(/Automatic inquiry messages are off\./)).toHaveLength(1);
    expect(screen.queryByRole('form', { name: 'Update inquiry follow-up' })).toBeNull();
    expect(api.update).not.toHaveBeenCalled();

    api.list.mockRejectedValueOnce({ message: 'Permission denied.' });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh queue' }));
    await screen.findByText('Permission denied.');
    expect(screen.queryByText(/Automatic inquiry messages are off\./)).toBeNull();
  });

  it.each([false, true])('prefers the collection switch over row fallback without hiding history (%s)', async (enabled) => {
    const inquiry = { id: INQUIRY, parent_name: 'Jordan Reed', email: 'jordan@example.org', stage: 'inquiry', notification_status: {
      enabled: false, notifications: [{ audience: 'family', channel: 'email', event: 'created', status: 'provider_accepted' }],
    } };
    api.list.mockResolvedValue({ results: [inquiry], owners: [], can_edit: false, notifications_enabled: enabled });
    api.detail.mockResolvedValue(inquiry);
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Jordan Reed' }));
    expect(screen.queryAllByText(/Automatic inquiry messages are off\./)).toHaveLength(enabled === false ? 1 : 0);
    const history = await screen.findByText('Communication status');
    fireEvent.click(history);
    expect(history.closest('details').open).toBe(true);
    expect(screen.getByText('Family · email · Accepted by provider')).toBeTruthy();
    expect(screen.getByText('You have read-only access to this queue.')).toBeTruthy();
    expect(screen.queryByRole('form', { name: 'Update inquiry follow-up' })).toBeNull();
    expect(api.update).not.toHaveBeenCalled();
  });

  it.each([false, true, undefined])('shows the off notice only for explicit false while retaining communication history (%s)', async (enabled) => {
    const notificationStatus = {
      notifications: [{ audience: 'family', channel: 'email', event: 'created', status: 'provider_accepted' }],
      ...(enabled === undefined ? {} : { enabled }),
    };
    const inquiry = { id: INQUIRY, parent_name: 'Jordan Reed', email: 'jordan@example.org', stage: 'inquiry', notification_status: notificationStatus };
    api.list.mockResolvedValue({ results: [inquiry], owners: [], can_edit: false });
    api.detail.mockResolvedValue(inquiry);
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Jordan Reed' }));
    await screen.findByText('Communication status');
    const note = screen.queryByText('Automatic inquiry messages are off. Review communication history before contacting this family.');
    if (enabled === false) expect(note).toBeTruthy();
    else expect(note).toBeNull();
    const history = await screen.findByText('Communication status');
    fireEvent.click(history);
    expect(history.closest('details').open).toBe(true);
    expect(screen.getByText('Family · email · Accepted by provider')).toBeTruthy();
    expect(api.update).not.toHaveBeenCalled();
  });

  it('shows family source conversion, actionable ownership, and explicit legacy attribution fallback', () => {
    const data = { inquiry_capture: { captured: 4, active: 1, unassigned: 1, followups_due: 0 }, inquiry_source_attribution: [{ source: 'Church referral', inquiries: 4, families_applied: 2, families_enrolled: 1, applications: 3, confirmed_applications: 2, inquiry_to_application_pct: 50, inquiry_to_enrollment_pct: 25 }], source_attribution: [{ source: 'Legacy source', applications: 8, enrolled: 2, conversion_pct: 25 }] };
    api.dashboard.mockImplementation(() => ({ data, source: 'live' }));
    const view = render(<MarketingDashboard />);
    const card = (key) => JSON.parse(screen.getByTestId('marketing-modules').textContent).find((item) => item.key === key);
    expect(card('sources').kpis).toEqual([{ label: 'Church referral · family inquiries', value: '4' }]);
    expect(card('sources').details).toEqual(['Church referral · Family inquiries: 4 · Families applied: 2 (50%) · Families enrolled: 1 (25%)']);
    expect(card('sources').summary).toContain('Both conversion rates use inquiring families');
    expect(card('inquiry-follow-up').status).toBe('Action Required');
    Object.assign(data.inquiry_capture, { unassigned: 0, followups_due: 1 }); view.rerender(<MarketingDashboard />);
    expect(card('inquiry-follow-up').status).toBe('Action Required');
    data.inquiry_capture.followups_due = 0; view.rerender(<MarketingDashboard />);
    expect(card('inquiry-follow-up').status).toBe('Ready');
    data.inquiry_source_attribution = []; view.rerender(<MarketingDashboard />);
    expect(card('sources').kpis).toEqual([]);
    delete data.inquiry_capture; delete data.inquiry_source_attribution; view.rerender(<MarketingDashboard />);
    expect(card('inquiry-follow-up').status).toBe('Unavailable');
    expect(card('sources').summary).toContain('Legacy application attribution');
    expect(card('sources').details).toEqual(['Legacy source: 8 child applications · 2 confirmed applications · 25% application-to-enrollment']);
  });

  it('saves an owner, due date, completed contact and reversible reminder pause', async () => {
    const inquiry = { id: INQUIRY, parent_name: 'Jordan Reed', email: 'jordan@example.org', grade_interest: '6', entry_year: '2029-2030', stage: 'inquiry', first_source: 'community_event', follow_up_consent: true, family_follow_up_enabled: true, application_ids: [] };
    api.list.mockImplementation(async () => ({ results: [inquiry], owners: [{ id: 'counselor-1', name: 'Pat Counselor' }], can_edit: true }));
    api.detail.mockImplementation(async () => inquiry);
    api.update.mockImplementation(async (_id, changes) => Object.assign(inquiry, changes));
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Jordan Reed' }));
    fireEvent.change(await screen.findByLabelText('Assigned counselor'), { target: { value: 'counselor-1' } });
    fireEvent.change(screen.getByLabelText('Next follow-up'), { target: { value: '2026-10-20T09:00' } });
    fireEvent.change(screen.getByLabelText('Contact summary'), { target: { value: 'Called family; offered a visit.' } });
    fireEvent.click(screen.getByLabelText(/Family follow-up reminders enabled/));
    fireEvent.click(screen.getByRole('button', { name: 'Save follow-up' }));
    await screen.findByText('Inquiry ownership and follow-up saved.');
    expect(api.update).toHaveBeenCalledWith(INQUIRY, expect.objectContaining({ assigned_to_user_id: 'counselor-1', next_follow_up_at: new Date('2026-10-20T09:00').toISOString(), family_follow_up_enabled: false, touchpoint: { channel: 'phone', summary: 'Called family; offered a visit.', outcome: '' } }));
    expect(api.update.mock.calls[0][1]).not.toHaveProperty('follow_up_consent');
    expect(api.list).toHaveBeenCalledTimes(2);
  });

  it('records a family stop request as consent withdrawal and prevents later staff re-enablement', async () => {
    const inquiry = { id: INQUIRY, parent_name: 'Jordan Reed', email: 'jordan@example.org', stage: 'inquiry', follow_up_consent: true, family_follow_up_enabled: true };
    api.list.mockImplementation(async () => ({ results: [inquiry], owners: [], can_edit: true }));
    api.detail.mockImplementation(async () => inquiry);
    api.update.mockImplementation(async (_id, changes) => Object.assign(inquiry, changes));
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Jordan Reed' }));
    expect((await screen.findByLabelText('Family asked to stop reminders')).checked).toBe(false);
    fireEvent.click(screen.getByLabelText('Family asked to stop reminders'));
    expect(screen.getByLabelText(/Family follow-up reminders enabled/).checked).toBe(false);
    expect(screen.getByLabelText(/Family follow-up reminders enabled/).disabled).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'Save follow-up' }));
    await screen.findByText('Inquiry ownership and follow-up saved.');
    expect(api.update).toHaveBeenCalledWith(INQUIRY, expect.objectContaining({ follow_up_consent: false, family_follow_up_enabled: false }));
    expect(screen.queryByLabelText('Family asked to stop reminders')).toBeNull();
    expect(screen.getByLabelText(/Family follow-up reminders enabled/).disabled).toBe(true);
    expect(screen.getByLabelText(/Family follow-up reminders enabled/).checked).toBe(false);
  });

  it('shows a denied or failed load without synthetic family records', async () => {
    api.list.mockRejectedValue({ message: 'Permission denied.' });
    render(<AdmissionsInquiryQueue />);
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText('Permission denied.')).toBeTruthy();
    expect(screen.queryByRole('table')).toBeNull();
    expect(screen.queryByText('Jordan Reed')).toBeNull();
    await waitFor(() => expect(api.list).toHaveBeenCalledTimes(1));
  });
});


describe('on-demand staff inquiry details', () => {
  it('does not render unverified details when the selected read is denied', async () => {
    const inquiry = { id: INQUIRY, parent_name: 'Jordan Reed', email: 'jordan@example.org', stage: 'inquiry' };
    api.list.mockResolvedValue({ results: [inquiry], owners: [], can_edit: true });
    api.detail.mockRejectedValueOnce({ message: 'Permission denied.' });
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Jordan Reed' }));
    expect(await screen.findByText('Permission denied.')).toBeTruthy();
    expect(screen.queryByRole('form', { name: 'Update inquiry follow-up' })).toBeNull();
    expect(api.detail).toHaveBeenCalledWith(INQUIRY);
  });
});

describe('staff inquiry pagination', () => {
  it('navigates to older inquiries without leaking details from the previous page', async () => {
    const first = { id: 'first-inquiry', parent_name: 'First Family', stage: 'inquiry' };
    const older = { id: 'older-inquiry', parent_name: 'Older Family', stage: 'inquiry' };
    api.list.mockImplementation(async ({ cursor }) => ({
      results: cursor === 'signed-next' ? [older] : [first],
      count: 101, next_cursor: cursor ? null : 'signed-next',
      page_size: 100, can_edit: false, owners: [],
    }));
    api.detail.mockImplementation(async (id) => id === first.id ? first : older);
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open First Family' }));
    await screen.findByText('You have read-only access to this queue.');
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(await screen.findByRole('button', { name: 'Open Older Family' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Open First Family' })).toBeNull();
    expect(screen.queryByText('You have read-only access to this queue.')).toBeNull();
    expect(api.list).toHaveBeenLastCalledWith({ stage: '', unassigned: '', overdue: '', cursor: 'signed-next' });
    fireEvent.click(screen.getByRole('button', { name: 'Previous page' }));
    expect(await screen.findByRole('button', { name: 'Open First Family' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(await screen.findByRole('button', { name: 'Open Older Family' })).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Unassigned'));
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({ stage: '', unassigned: 1, overdue: '' }));
  });
});


describe('inquiry detail response identity and concurrent selection', () => {
  it('never displays an older family after the user selects a different family', async () => {
    const first = { id: 'first-family', parent_name: 'First Family', stage: 'inquiry' };
    const second = { id: 'second-family', parent_name: 'Second Family', stage: 'inquiry' };
    let resolveFirst;
    api.list.mockResolvedValue({ results: [first, second], owners: [], can_edit: false });
    api.detail.mockImplementation((id) => id === first.id
      ? new Promise((resolve) => { resolveFirst = resolve; })
      : Promise.resolve(second));
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open First Family' }));
    await waitFor(() => expect(api.detail).toHaveBeenCalledWith(first.id));
    fireEvent.click(screen.getByRole('button', { name: 'Open Second Family' }));
    expect(await screen.findByRole('region', { name: 'Inquiry details for Second Family' })).toBeTruthy();
    await act(async () => { resolveFirst(first); });
    expect(screen.queryByRole('region', { name: 'Inquiry details for First Family' })).toBeNull();
    expect(screen.getByRole('region', { name: 'Inquiry details for Second Family' })).toBeTruthy();
  });

  it('rejects a successful response whose inquiry identity does not match the selected row', async () => {
    const inquiry = { id: 'selected-family', parent_name: 'Selected Family', stage: 'inquiry' };
    api.list.mockResolvedValue({ results: [inquiry], owners: [], can_edit: true });
    api.detail.mockResolvedValue({ id: 'other-family', parent_name: 'Other Family', stage: 'inquiry' });
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Open Selected Family' }));
    expect((await screen.findByRole('alert')).textContent).toContain('did not match the selected family');
    expect(screen.queryByRole('form', { name: 'Update inquiry follow-up' })).toBeNull();
  });
});

describe('inquiry paging recovery', () => {
  it('returns to the previous page when concurrent changes empty the current cursor page', async () => {
    const first = { id: 'first-family', parent_name: 'First Family', stage: 'inquiry' };
    api.list.mockImplementation(async ({ cursor }) => ({
      results: cursor ? [] : [first], count: 1, next_cursor: cursor ? null : 'signed-next',
      owners: [], can_edit: false,
    }));
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Next page' }));
    await screen.findByText('No inquiries remain on this page.');
    fireEvent.click(screen.getByRole('button', { name: 'Previous page' }));
    expect(await screen.findByRole('button', { name: 'Open First Family' })).toBeTruthy();
  });

  it('allows recovery from an expired or invalid signed page cursor', async () => {
    const first = { id: 'first-family', parent_name: 'First Family', stage: 'inquiry' };
    api.list.mockImplementation(({ cursor }) => cursor
      ? Promise.reject(new Error('Invalid, expired, or mismatched inquiry page cursor.'))
      : Promise.resolve({ results: [first], count: 1, next_cursor: 'signed-next', owners: [], can_edit: false }));
    render(<AdmissionsInquiryQueue />);
    fireEvent.click(await screen.findByRole('button', { name: 'Next page' }));
    await screen.findByText('Invalid, expired, or mismatched inquiry page cursor.');
    fireEvent.click(screen.getByRole('button', { name: 'Return to first page' }));
    expect(await screen.findByRole('button', { name: 'Open First Family' })).toBeTruthy();
  });
});
