// @vitest-environment jsdom
// Actual wizardRoutes -> RoleRouteGuard -> ReleaseStateRoute composition.
// All wizard components are synthetic stubs: no API calls, users, or writes.
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router';

import { DEV_AID_PREVIEW_ORIGIN } from '../components/routing/devAidPreviewAccess.js';

vi.mock('../pages/FinancialAidWizard.jsx', () => ({
  default: () => <div data-testid="aid-wizard-route">Synthetic aid wizard</div>,
}));
vi.mock('../pages/BillingWizard.jsx', () => ({
  default: () => <div data-testid="billing-wizard-route">Synthetic billing wizard</div>,
}));

let wizardRoutes;

beforeAll(async () => {
  // The broad certification escape hatch is evaluated at import time.
  // Disable it BEFORE importing the real route wrappers.
  vi.stubEnv('VITE_WIZARD_CERTIFICATION', '0');
  ({ wizardRoutes } = await import('./wizards.js'));
});

beforeEach(() => {
  vi.stubEnv('VITE_WIZARD_CERTIFICATION', '0');
  vi.stubEnv('VITE_DEV_AID_WIZARD_PREVIEW', '1');
  vi.stubEnv('VITE_SANDBOX_MODE', '1');
  vi.stubEnv('VITE_DEMO_MODE', 'sandbox');
  vi.stubGlobal('location', { origin: DEV_AID_PREVIEW_ORIGIN });
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  delete globalThis.__CROWN_USER_ROLES__;
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

function renderWizard(path, role) {
  globalThis.__CROWN_USER_ROLES__ = role ? [role] : [];

  const router = createMemoryRouter(
    [
      ...wizardRoutes(),
      { path: '/not-authorized', element: <div data-testid="role-denied">Role denied</div> },
      { path: '/wizards', element: <div data-testid="draft-denied">Draft gated</div> },
      { path: '*', element: <div data-testid="unmatched">Unmatched route</div> },
    ],
    { initialEntries: [path] },
  );

  render(<RouterProvider router={router} />);
  return router;
}

describe('actual guarded DEV Financial Aid wizard route', () => {
  it('renders the draft aid wizard for an authorized synthetic finance role only on the isolated preview', async () => {
    const router = renderWizard('/aid-setup', 'finance_admin');
    expect(await screen.findByTestId('aid-wizard-route')).toBeTruthy();
    expect(router.state.location.pathname).toBe('/aid-setup');
  });

  it('keeps the real role guard active even when the release preview switch is enabled', async () => {
    const router = renderWizard('/aid-setup', 'parent');
    await waitFor(() => expect(router.state.location.pathname).toBe('/not-authorized'));
    expect(screen.getByTestId('role-denied')).toBeTruthy();
    expect(screen.queryByTestId('aid-wizard-route')).toBeNull();
  });

  it.each(['', '0'])('redirects the authorized role when the preview opt-in is %j', async (flag) => {
    vi.stubEnv('VITE_DEV_AID_WIZARD_PREVIEW', flag);
    const router = renderWizard('/aid-setup', 'finance_admin');
    await waitFor(() => expect(router.state.location.pathname).toBe('/wizards'));
    expect(screen.getByTestId('draft-denied')).toBeTruthy();
    expect(screen.queryByTestId('aid-wizard-route')).toBeNull();
  });

  it('redirects the authorized role when the page origin is not the exact DEV preview', async () => {
    vi.stubGlobal('location', { origin: 'https://untrusted.invalid' });
    const router = renderWizard('/aid-setup', 'finance_admin');
    await waitFor(() => expect(router.state.location.pathname).toBe('/wizards'));
    expect(screen.getByTestId('draft-denied')).toBeTruthy();
    expect(screen.queryByTestId('aid-wizard-route')).toBeNull();
  });

  it.each([
    ['disabled sandbox', 'VITE_SANDBOX_MODE', '0'],
    ['production demo mode', 'VITE_DEMO_MODE', 'production'],
  ])('redirects the authorized role with %s', async (_label, envName, value) => {
    vi.stubEnv(envName, value);
    const router = renderWizard('/aid-setup', 'finance_admin');
    await waitFor(() => expect(router.state.location.pathname).toBe('/wizards'));
    expect(screen.getByTestId('draft-denied')).toBeTruthy();
    expect(screen.queryByTestId('aid-wizard-route')).toBeNull();
  });

  it('never exposes a different draft wizard through the aid-only preview flag', async () => {
    const router = renderWizard('/billing-setup', 'finance_admin');
    await waitFor(() => expect(router.state.location.pathname).toBe('/wizards'));
    expect(screen.getByTestId('draft-denied')).toBeTruthy();
    expect(screen.queryByTestId('billing-wizard-route')).toBeNull();
  });
});
