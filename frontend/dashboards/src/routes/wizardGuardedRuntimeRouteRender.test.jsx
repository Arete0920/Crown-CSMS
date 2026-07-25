// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RouterProvider, createMemoryRouter } from 'react-router';

import WizardHub from '../pages/WizardHub.jsx';
import { isProductionReady } from '../config/releaseState.js';
import { WIZARD_MANIFEST } from './wizard-manifest.js';
import { WIZARD_REGISTRY, wizardRoutes } from './wizards.js';

vi.mock('../components/brand/CrownLogo', () => ({
  default: () => 'CROWN',
}));

vi.mock('../api/wizards', () => ({
  fetchWizards: async () => ({
    wizards: [
      { slug: 'student-import-wizard', title: 'Student Import', enabled: true },
      { slug: 'guardian-household-wizard', title: 'Guardian & Household Setup', enabled: true },
      { slug: 'section-staffing-wizard', title: 'Section Staffing', enabled: true },
      { slug: 'attendance-codes-wizard', title: 'Attendance Codes Setup', enabled: true },
      { slug: 'grade-weights-wizard', title: 'Grade Weights & Categories', enabled: true },
    ],
  }),
}));

const ALL_WIZARD_ROLES = [
  ...new Set(WIZARD_REGISTRY.flatMap((route) => route.roles || [])),
];

function fallbackRoutes() {
  return [
    {
      path: '/not-authorized',
      element: <div>NOT AUTHORIZED</div>,
    },
    {
      path: '/unavailable',
      element: <div>UNAVAILABLE</div>,
    },
    {
      path: '/wizards',
      element: <WizardHub />,
    },
    {
      path: '*',
      element: <div>UNMATCHED</div>,
    },
  ];
}

function seedAuthorizedRoles() {
  const roles = JSON.stringify(ALL_WIZARD_ROLES);
  localStorage.setItem('crown_user_roles', roles);
  sessionStorage.setItem('crown_user_roles', roles);
  globalThis.__CROWN_USER_ROLES__ = ALL_WIZARD_ROLES;
}

function renderAt(path) {
  const router = createMemoryRouter([...wizardRoutes(), ...fallbackRoutes()], {
    initialEntries: [path],
  });

  render(<RouterProvider router={router} />);
  return router;
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  sessionStorage.clear();
  localStorage.clear();
  seedAuthorizedRoles();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  delete globalThis.__CROWN_USER_ROLES__;
});

describe('wizard guarded runtime route rendering', () => {
  it('has a non-empty authorized wizard role set for guarded routes', () => {
    expect(ALL_WIZARD_ROLES.length).toBeGreaterThan(0);
  });

  it('renders every unique wizard browser path with RoleRouteGuard and ReleaseStateRoute active', async () => {
    const uniquePaths = [...new Set(WIZARD_MANIFEST.map((entry) => entry.path))];

    expect(uniquePaths).toHaveLength(28);

    for (const path of uniquePaths) {
      cleanup();
      seedAuthorizedRoles();

      const router = renderAt(path);

      await waitFor(() => {
        const bodyText = document.body.textContent.replace(/\s+/g, ' ').trim();

        expect(router.state.location.pathname, `${path} should not redirect to not-authorized`).not.toBe('/not-authorized');
        expect(bodyText, `${path} should not render not-authorized fallback`).not.toContain('NOT AUTHORIZED');
        expect(bodyText, `${path} should not render unavailable fallback`).not.toContain('UNAVAILABLE');
        expect(bodyText, `${path} should not render unmatched fallback`).not.toContain('UNMATCHED');
        expect(bodyText.length, `${path} should render guarded content`).toBeGreaterThan(0);
      });
    }
  });

  it('renders WizardHub-backed production-ready wizard routes with guarded wrappers active', async () => {
    const wizardHubRoutes = WIZARD_REGISTRY.filter((route) => route.component === WizardHub);

    const readyWizardHubPaths = wizardHubRoutes
      .filter((route) => isProductionReady(route))
      .map((route) => route.path);

    const nonReadyWizardHubPaths = wizardHubRoutes
      .filter((route) => !isProductionReady(route))
      .map((route) => route.path);

    for (const path of nonReadyWizardHubPaths) {
      cleanup();
      seedAuthorizedRoles();

      const router = renderAt(path);

      await waitFor(() => {
        expect(
          router.state.location.pathname,
          `non-ready WizardHub route ${path} should redirect away`,
        ).not.toBe(path);
      });
    }

    for (const path of readyWizardHubPaths) {
      cleanup();
      seedAuthorizedRoles();
      renderAt(path);

      expect(await screen.findByText('Wizard Hub')).toBeTruthy();
      expect(await screen.findByText('Student Import')).toBeTruthy();
      expect(await screen.findByText('Guardian & Household Setup')).toBeTruthy();
      expect(await screen.findByText('Section Staffing')).toBeTruthy();
      expect(await screen.findByText('Attendance Codes Setup')).toBeTruthy();
      expect(await screen.findByText('Grade Weights & Categories')).toBeTruthy();
    }
  });
});
