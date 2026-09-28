import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { BUYER_WALKTHROUGH } from '../sandbox/buyerWalkthrough';

const DASHBOARD_ONLY_SUFFIX = /dashboard$/;
const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function routeHasWorkflowDepth(route) {
  return !DASHBOARD_ONLY_SUFFIX.test(route.replace(/\/$/, ''));
}

function readSource(relativePath) {
  return readFileSync(path.resolve(sourceRoot, relativePath), 'utf8');
}

describe('buyer walkthrough contract', () => {
  it('uses one passwordless sandbox entry without exposing protected pages publicly', () => {
    expect(BUYER_WALKTHROUGH.entryRoute).toBe('/sandbox');
    expect(BUYER_WALKTHROUGH.passwordless).toBe(true);
    expect(BUYER_WALKTHROUGH.school).toBe('Heritage Christian Academy');
  });

  it('keeps the approved CROWN visual system as the design authority', () => {
    expect(BUYER_WALKTHROUGH.designAuthority).toEqual(expect.arrayContaining([
      'styles/crown-theme.css',
      'styles/launch-shell.css',
      'styles/client-experience.css',
      'components/crown-dashboard/CrownDashboardTemplate.jsx',
    ]));
  });

  it('loads the canonical visual system application-wide', () => {
    const main = readSource('main.jsx');
    expect(sourceRoot).toContain('src');
    expect(main).toContain("import './styles/crown-theme.css'");
    expect(main).toContain("import './styles/crown.css'");
    expect(main).toContain("import './styles/launch-shell.css'");
    expect(main).toContain("import './styles/client-experience.css'");
    expect(main).toContain('<ThemeProvider theme={crownTheme}>');
  });

  it('preserves the canonical KPI/widget composition for command surfaces', () => {
    const template = readSource('components/crown-dashboard/CrownDashboardTemplate.jsx');
    for (const component of [
      'CrownDashboardMetricGrid',
      'CrownDashboardMetricCard',
      'CrownInsightPanel',
      'CrownQuickActions',
      'CrownDashboardActivityFeed',
      'CrownDashboardStatusPanel',
      'CrownDashboardRightRail',
      'CrownDashboardDataTruthStatus',
      'CrownDashboardDecisionPanel',
    ]) {
      expect(template).toContain(component);
    }
  });

  it('covers all six buyer personas with workflow depth beyond dashboards', () => {
    const personas = BUYER_WALKTHROUGH.journeys.map((journey) => journey.persona);
    expect(personas).toEqual(expect.arrayContaining([
      'school_admin',
      'admissions_director',
      'finance_director',
      'teacher',
      'parent',
      'student',
    ]));

    for (const journey of BUYER_WALKTHROUGH.journeys) {
      expect(journey.routes.length).toBeGreaterThanOrEqual(4);
      expect(journey.proofPoints.length).toBeGreaterThanOrEqual(4);
      expect(journey.routes.some(routeHasWorkflowDepth)).toBe(true);
      expect(journey.routes).not.toContain('/login');
      expect(journey.routes.every((route) => route.startsWith('/'))).toBe(true);
    }
  });

  it('does not encode credentials or predecessor repository authority', () => {
    const { passwordless, ...publicData } = BUYER_WALKTHROUGH;
    expect(passwordless).toBe(true);
    const serialized = JSON.stringify(publicData).toLowerCase();
    expect(serialized).not.toContain('password');
    expect(serialized).not.toContain('tcmegahan/crown2026');
    expect(serialized).not.toContain('crown2026');
  });
});
