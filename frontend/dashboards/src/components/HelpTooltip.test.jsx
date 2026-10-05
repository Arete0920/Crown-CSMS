import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router';
import { HelpTooltip } from './HelpTooltip';
import SolomonContextHelp from './SolomonContextHelp';
import { apiFetch } from '../lib/api';
vi.mock('../lib/api', () => ({ apiFetch: vi.fn() }));
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
  apiFetch.mockReset();
});
afterEach(() => { cleanup(); vi.unstubAllEnvs(); sessionStorage.clear(); localStorage.clear(); });
const reply = (data, status = 200) => ({ ok: status === 200, status, json: async () => data });

describe('Solomon contextual help', () => {
  it('loads on demand, displays published text safely, and returns focus on close', async () => {
    apiFetch.mockResolvedValue(reply({ title: 'Review invoices', content: '<script>unsafe</script>\nReview totals.' }));
    render(<HelpTooltip slug="billing-guide" />);
    expect(apiFetch).not.toHaveBeenCalled();
    expect(document.querySelector('.solomon-help-panel h2')).toBeNull();
    const button = screen.getByRole('button', { name: 'Help from Solomon' });
    fireEvent.click(button);
    await screen.findByRole('heading', { name: 'Review invoices' });
    expect(document.querySelector('.solomon-help-article script')).toBeNull();
    expect(apiFetch.mock.calls[0][0]).toBe('/api/v1/help/billing-guide/');
    fireEvent.click(screen.getByRole('button', { name: 'Close help' }));
    expect(button.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(button);
  });
  it('reports errors and retries instead of presenting failed payloads as guidance', async () => {
    apiFetch.mockResolvedValueOnce(reply({}, 403)).mockResolvedValueOnce(reply({ title: 'Help', content: 'Ready' }));
    render(<HelpTooltip slug="private" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Try again' }));
    await screen.findByText('Ready');
  });
  it('shows a truthful empty state', async () => {
    apiFetch.mockResolvedValue(reply({}, 404));
    render(<HelpTooltip slug="missing" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText(/No published guidance/);
  });
  it('sends only fixed route metadata, excluding record IDs and query data', async () => {
    apiFetch.mockResolvedValue(reply({ primary_article: { title: 'Billing help', content: 'Review invoices.' } }));
    render(<MemoryRouter initialEntries={['/billing/individual-secret?student=private&balance=100']}><SolomonContextHelp /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText('Review invoices.');
    expect(apiFetch.mock.calls[0][0]).toBe('/api/v1/solomon/context/?route_path=%2Fbilling&module=billing');
  });
  it('cancels requests on dismissal and ignores late responses', async () => {
    let resolve;
    apiFetch.mockReturnValue(new Promise(r => { resolve = r; }));
    render(<HelpTooltip slug="slow" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close help' }));
    expect(apiFetch.mock.calls[0][1].signal.aborted).toBe(true);
    resolve(reply({ title: 'Late', content: 'Must not display' }));
    await waitFor(() => expect(screen.queryByText('Must not display')).toBeNull());
  });
});

describe('fixed Solomon page contexts', () => {
  it.each([
    ['/admissions/start', '/admissions', 'admissions'],
    ['/billing-setup', '/billing', 'billing'],
    ['/finance', '/billing', 'billing'],
    ['/financial-aid-dashboard', '/financial-aid', 'financial_aid'],
    ['/onboarding', '/onboarding', 'onboarding'],
    ['/students/private-record?name=private', '/dashboard', null],
  ])('maps %s without transmitting user data', async (path, route, module) => {
    apiFetch.mockResolvedValue(reply({}, 404));
    render(<MemoryRouter initialEntries={[path]}><SolomonContextHelp /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText(/No published guidance/);
    const params = new URLSearchParams({ route_path: route, ...(module ? { module } : {}) });
    expect(apiFetch.mock.calls[0][0]).toBe(`/api/v1/solomon/context/?${params}`);
    expect(apiFetch.mock.calls[0][1].validateStatus(404)).toBe(true);
    expect(apiFetch.mock.calls[0][1].validateStatus(403)).toBe(false);
  });
});

describe('Meet Solomon introduction', () => {
  it('explains his role and returns to the same page guidance without another request', async () => {
    apiFetch.mockResolvedValue(reply({ title: 'Billing directions', content: 'Review your totals.' }));
    render(<HelpTooltip slug="billing-guide" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText('Review your totals.');
    fireEvent.click(screen.getByRole('button', { name: 'Meet Solomon' }));
    expect(screen.getByRole('heading', { name: 'Meet Solomon' })).toBeTruthy();
    expect(screen.getByText(/your guide to CROWN/)).toBeTruthy();
    expect(screen.getByText(/get help navigating CROWN/)).toBeTruthy();
    expect(screen.queryByText('Review your totals.')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Back to page help' }));
    expect(screen.getByText('Review your totals.')).toBeTruthy();
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });
  it('can introduce Solomon even when published topic guidance is absent', async () => {
    apiFetch.mockResolvedValue(reply({}, 404));
    render(<HelpTooltip slug="missing" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText(/No published guidance/);
    fireEvent.click(screen.getByRole('button', { name: 'Meet Solomon' }));
    expect(screen.getByRole('heading', { name: 'Meet Solomon' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close help' }));
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    expect(screen.queryByRole('heading', { name: 'Meet Solomon' })).toBeNull();
  });
});


describe('optional structured staff guidance', () => {
  const guidance = { topic: 'onboarding', title: 'Implementation guidance', guidance: 'Review school roles.',
    mode: 'curated_guidance', generated_by_ai: false, human_review_required: true };
  const setup = (role = 'teacher') => {
    vi.stubEnv('VITE_SOLOMON_GUIDANCE_ENABLED', 'true');
    sessionStorage.setItem('crown.role', role);
    apiFetch.mockResolvedValue(reply({}, 404));
    render(<HelpTooltip slug="missing" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
  };
  it('remains hidden by default even for staff', async () => {
    sessionStorage.setItem('crown.role', 'teacher');
    apiFetch.mockResolvedValue(reply({}, 404));
    render(<HelpTooltip slug="missing" />);
    fireEvent.click(screen.getByRole('button', { name: 'Help from Solomon' }));
    await screen.findByText(/No published guidance/);
    expect(screen.queryByRole('region', { name: 'General staff guidance' })).toBeNull();
  });
  it.each(['parent', 'student', 'unknown'])('does not expose staff guidance to %s', async role => {
    setup(role);
    await screen.findByText(/No published guidance/);
    expect(screen.queryByRole('region', { name: 'General staff guidance' })).toBeNull();
  });
  it('requires review acknowledgement and sends only the selected topic', async () => {
    setup();
    await screen.findByText(/No published guidance/);
    const view = screen.getByRole('button', { name: 'View guidance' });
    expect(view.disabled).toBe(true);
    expect(screen.queryByRole('textbox')).toBeNull();
    fireEvent.click(screen.getByRole('checkbox', { name: /I will review/ }));
    apiFetch.mockResolvedValue(reply(guidance));
    fireEvent.click(view);
    await screen.findByText('Review school roles.');
    const [path, options] = apiFetch.mock.calls.at(-1);
    expect(path).toBe('/api/solomon/guidance/');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ topic: 'onboarding', human_review_acknowledged: true });
    expect(screen.getByText(/Curated CROWN guidance/)).toBeTruthy();
    fireEvent.change(screen.getByRole('combobox', { name: 'Guidance topic' }), { target: { value: 'strategy' } });
    expect(screen.queryByText('Review school roles.')).toBeNull();
    expect(view.disabled).toBe(true);
  });
  it('rejects generated or mismatched responses instead of presenting them', async () => {
    setup();
    await screen.findByText(/No published guidance/);
    apiFetch.mockResolvedValue(reply({ ...guidance, generated_by_ai: true, guidance: 'Must not show' }));
    fireEvent.click(screen.getByRole('checkbox', { name: /I will review/ }));
    fireEvent.click(screen.getByRole('button', { name: 'View guidance' }));
    await screen.findByText(/Guidance could not be loaded/);
    expect(screen.queryByText('Must not show')).toBeNull();
  });
  it('explains a disabled backend without inventing advice', async () => {
    setup();
    await screen.findByText(/No published guidance/);
    fireEvent.click(screen.getByRole('checkbox', { name: /I will review/ }));
    fireEvent.click(screen.getByRole('button', { name: 'View guidance' }));
    await screen.findByText(/Staff guidance is not enabled/);
  });
  it('aborts pending guidance when the dialog is closed', async () => {
    setup();
    await screen.findByText(/No published guidance/);
    let resolve;
    apiFetch.mockReturnValue(new Promise(r => { resolve = r; }));
    fireEvent.click(screen.getByRole('checkbox', { name: /I will review/ }));
    fireEvent.click(screen.getByRole('button', { name: 'View guidance' }));
    const options = apiFetch.mock.calls.at(-1)[1];
    fireEvent.click(screen.getByRole('button', { name: 'Close help' }));
    expect(options.signal.aborted).toBe(true);
    resolve(reply(guidance));
    await waitFor(() => expect(screen.queryByText('Review school roles.')).toBeNull());
  });
});
