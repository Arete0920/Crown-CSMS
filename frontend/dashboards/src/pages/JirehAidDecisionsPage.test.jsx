import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { apiJson } from '../lib/api.js';
import { setAccessToken, setSelectedSchoolId } from '../utils/authClient.js';
import JirehAidDecisionsPage from './JirehAidDecisionsPage.jsx';

vi.mock('../lib/api.js', () => ({ apiJson: vi.fn() }));
vi.mock('../components/crown/CrownLayout.jsx', () => ({
  default: ({ children }) => <main>{children}</main>,
}));

const SCHOOL = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const OTHER = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const YEAR = '11111111-1111-4111-8111-111111111111';
const SUMMARY = '/api/v1/dashboards/financial-aid/summary';
const OVERVIEW = '/api/aid/admin/overview/?academic_year_id=' + YEAR;
const live = (schoolId = SCHOOL) => ({
  dashboard_key: 'financial-aid',
  meta: { served_from: 'live_db', school_id: schoolId, academic_year_id: YEAR },
});
const application = (id = 7, schoolId = SCHOOL) => ({
  id, school_id: schoolId, academic_year_id: YEAR, status: 'SUBMITTED', household_size: 3,
});
const overview = (applications = [application()]) => ({ applications, awards: [], budgets: [] });
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};

beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.clear(); localStorage.clear();
  setAccessToken('fictional-officer-A');
  setSelectedSchoolId(SCHOOL);
  apiJson.mockImplementation(async (path) => {
    if (path === SUMMARY) return live();
    if (path === OVERVIEW) return overview();
    throw new Error('Unexpected request: ' + path);
  });
});
afterEach(() => {
  cleanup();
  sessionStorage.clear(); localStorage.clear();
});

describe('Jireh officer live-year initialization', () => {
  it('opens the case queue from live aid metadata without classroom access or an invented year name', async () => {
    render(<JirehAidDecisionsPage />);
    expect(await screen.findByRole('button', { name: /Application #7/ })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Current aid year: Verified (live)' })).toBeTruthy();
    expect(screen.queryByText(/2026-2027/)).toBeNull();
    expect(apiJson.mock.calls.map(([path]) => path)).toEqual([SUMMARY, OVERVIEW, SUMMARY]);
    expect(apiJson.mock.calls.some(([path]) => path.includes('/academics/years/'))).toBe(false);
    expect(apiJson.mock.calls.every(([, options]) => !options?.method || options.method === 'GET')).toBe(true);
  });

  it.each([
    ['sample', { ...live(), meta: { ...live().meta, served_from: 'sample' } }],
    ['snapshot', { ...live(), meta: { ...live().meta, served_from: 'snapshot' } }],
    ['foreign school', live(OTHER)],
    ['missing year', { ...live(), meta: { ...live().meta, academic_year_id: null } }],
    ['malformed year', { ...live(), meta: { ...live().meta, academic_year_id: '2026-2027' } }],
    ['wrong dashboard', { ...live(), dashboard_key: 'academics' }],
  ])('fails closed on %s bootstrap metadata without reading or displaying awards', async (_case, payload) => {
    apiJson.mockResolvedValue(payload);
    render(<JirehAidDecisionsPage />);
    expect((await screen.findByRole('alert')).textContent).toContain('live Financial Aid summary');
    expect(screen.getByRole('heading', { name: 'Current aid year: Not verified' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Application #/ })).toBeNull();
    expect(screen.queryByText(/Current-year accepted awards:/)).toBeNull();
    expect(apiJson.mock.calls.map(([path]) => path)).toEqual([SUMMARY]);
  });

  it('stops on financial-aid permission denial without trying another endpoint', async () => {
    apiJson.mockRejectedValue({ response: { status: 403, data: { detail: 'Permission denied.' } } });
    render(<JirehAidDecisionsPage />);
    expect((await screen.findByRole('alert')).textContent).toBe('Permission denied.');
    expect(apiJson.mock.calls.map(([path]) => path)).toEqual([SUMMARY]);
    expect(screen.queryByRole('button', { name: /Application #/ })).toBeNull();
  });

  it.each(['token', 'school'])('requires a verified %s before any request', async (missing) => {
    if (missing === 'token') setAccessToken('');
    else setSelectedSchoolId('');
    render(<JirehAidDecisionsPage />);
    expect((await screen.findByRole('alert')).textContent).toContain('verified school session');
    expect(apiJson).not.toHaveBeenCalled();
  });

  it.each(['token', 'school'])('discards a bootstrap response after the %s changes', async (changed) => {
    const old = deferred();
    const replacement = deferred();
    apiJson.mockReturnValueOnce(old.promise);
    apiJson.mockReturnValue(replacement.promise);
    render(<JirehAidDecisionsPage />);
    await act(async () => {
      if (changed === 'token') setAccessToken('fictional-officer-B');
      else setSelectedSchoolId(OTHER);
    });
    await act(async () => { old.resolve(live()); });
    expect(apiJson.mock.calls.some(([path]) => path === OVERVIEW)).toBe(false);
    expect(screen.getByRole('heading', { name: 'Current aid year: Not verified' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Application #7/ })).toBeNull();
    const schoolId = changed === 'school' ? OTHER : SCHOOL;
    apiJson.mockImplementation(async (path) => path === SUMMARY ? live(schoolId) : overview([application(8, schoolId)]));
    await act(async () => { replacement.resolve(live(schoolId)); });
    expect(await screen.findByRole('button', { name: /Application #8/ })).toBeTruthy();
  });

  it('discards a bootstrap response after unmount', async () => {
    const old = deferred();
    apiJson.mockReturnValue(old.promise);
    const view = render(<JirehAidDecisionsPage />);
    view.unmount();
    await act(async () => { old.resolve(live()); });
    expect(apiJson.mock.calls.map(([path]) => path)).toEqual([SUMMARY]);
  });

  it('rejects foreign-school financial records after a valid bootstrap', async () => {
    apiJson.mockImplementation(async (path) => path === SUMMARY ? live() : overview([application(99, OTHER)]));
    render(<JirehAidDecisionsPage />);
    expect((await screen.findByRole('alert')).textContent).toContain('inconsistent school/year');
    expect(screen.queryByRole('button', { name: /Application #99/ })).toBeNull();
  });

  it('drops an in-flight overview and clears displayed cases when the session changes', async () => {
    const old = deferred();
    render(<JirehAidDecisionsPage />);
    await screen.findByRole('button', { name: /Application #7/ });
    apiJson.mockImplementation((path) => path === OVERVIEW ? old.promise : Promise.resolve(live()));
    fireEvent.click(screen.getByRole('button', { name: 'Refresh and reconcile records' }));
    await waitFor(() => expect(apiJson).toHaveBeenCalledWith(OVERVIEW));
    await act(async () => { setAccessToken(''); });
    expect(screen.queryByRole('button', { name: /Application #7/ })).toBeNull();
    await act(async () => { old.resolve(overview([application(99)])); });
    expect(screen.queryByRole('button', { name: /Application #99/ })).toBeNull();
    expect(screen.getByRole('heading', { name: 'Current aid year: Not verified' })).toBeTruthy();
  });
});
