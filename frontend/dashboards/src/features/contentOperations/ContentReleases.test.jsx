import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ContentReleaseWorkbench, FamilyReleaseFeed } from './ContentReleases.jsx';
import { crownApiClient } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { request: vi.fn() } }));
const metrics = { recipients: 1, email_accepted: 0, email_pending: 1, email_dead: 0, attempts: 0, acknowledged: 0, responses: { returning: 0, declining: 0, undecided: 0 } };
const release = { id: 'release-1', title: 'School notice', status: 'draft', revision: 1, blocks: [{ type: 'action', title: 'Plans', body: 'Please respond' }], metrics };
beforeEach(() => { crownApiClient.request.mockReset(); });
afterEach(cleanup);
describe('Content releases', () => {
  it('requires saved preview before approval and shows actual audience', async () => {
    crownApiClient.request.mockImplementation(async ({ url }) => ({ data: url.endsWith('/preview/') ? { title: 'School notice', school: 'School', year: '2027', deadline: '2027-03-01', blocks: release.blocks, resources: [], fingerprint: 'proof', recipients: 1, portal_recipients: 1, email_recipients: 1 } : [release] }));
    render(<ContentReleaseWorkbench sessionId="session-1" />);
    fireEvent.click(await screen.findByText('School notice · draft · version 1'));
    expect(screen.getByText('Approve preview and schedule').disabled).toBe(true);
    fireEvent.click(screen.getByText('Preview saved release'));
    await screen.findByText('Preview audience: 1 guardians · 1 emails · 1 portal accounts');
    expect(screen.getByText('Approve preview and schedule').disabled).toBe(false);
    fireEvent.change(screen.getByLabelText('Release title'), { target: { value: 'Changed' } });
    expect(screen.getByText('Approve preview and schedule').disabled).toBe(true);
  });
  it('sends guardian intent without claiming enrollment completion', async () => {
    crownApiClient.request.mockResolvedValue({ data: [{ ...release, school: 'School', year: '2027', deadline: '2027-03-01', resources: [], response: '' }] });
    render(<FamilyReleaseFeed />);
    fireEvent.click(await screen.findByText('returning'));
    await waitFor(() => expect(crownApiClient.request).toHaveBeenCalledWith(expect.objectContaining({ url: '/api/comms/family-releases/release-1/respond/', data: { response: 'returning' } })));
    expect(screen.getByText(/does not complete enrollment/)).toBeTruthy();
  });
  it('displays access errors instead of a success state', async () => {
    crownApiClient.request.mockRejectedValue({ response: { data: { detail: 'Permission denied' } } });
    render(<FamilyReleaseFeed />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Permission denied');
  });
  it('keeps parent and staff pages usable when a list endpoint returns an object', async () => {
    crownApiClient.request.mockResolvedValue({ data: { detail: 'Endpoint unavailable' } });
    render(<FamilyReleaseFeed />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'School notices are temporarily unavailable. Please try again.');
    cleanup();
    render(<ContentReleaseWorkbench sessionId="session-1" />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'School notices are temporarily unavailable. Please try again.');
    expect(screen.getByText('Save draft')).toBeTruthy();
  });

});
