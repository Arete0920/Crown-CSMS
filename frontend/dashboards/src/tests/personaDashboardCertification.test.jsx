// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { DASHBOARD_TEMPLATE_MAP } from '../config/dashboardTemplates/index.js';
import { BASE_NOTE } from '../config/dashboardTemplates/_baseData.js';

const PRODUCTION_PERSONA_KEYS = [
  'schoolAdministrator',
  'teacher',
  'parent',
  'student',
  'admissions',
  'attendance',
  'gradebook',
  'finance',
  'communications',
  'board',
  'it',
  'marketing',
  'spiritualLife',
  'office',
  'health',
  'counseling',
  'food',
  'athletics',
  'registrar',
  'billing',
  'financialAid',
  'scheduling',
  'studentCare',
  'activitiesAthletics',
  'advancement',
  'hr',
  'facilities',
  'transportation',
  'fineArts',
  'libraryMedia',
  'extendedCare',
  'safetySecurity',
  'curriculumPD',
];

function renderPersonaDashboard(personaKey) {
  const config = DASHBOARD_TEMPLATE_MAP[personaKey];

  if (!config) {
    throw new Error(`Missing dashboard template for persona: ${personaKey}`);
  }

  return render(
    <MemoryRouter>
      <CrownDashboardTemplate config={config} roleKey={personaKey} />
    </MemoryRouter>,
  );
}

function normalizedText(container) {
  return container.textContent.replace(/\s+/g, ' ').trim();
}

afterEach(() => {
  cleanup();
});

describe('persona dashboard certification', () => {
  it('certifies all required production persona templates exist', () => {
    const missing = PRODUCTION_PERSONA_KEYS.filter((key) => !DASHBOARD_TEMPLATE_MAP[key]);
    expect(missing).toEqual([]);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s renders the shared faith/community surface', (personaKey) => {
    const { container } = renderPersonaDashboard(personaKey);
    const text = normalizedText(container);

    expect(text).toMatch(/devotion|scripture|proverbs|prayer/i);
    expect(text).toMatch(/prayer/i);
    expect(text).toMatch(/announcement/i);
    expect(text).toMatch(/celebration/i);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s renders the shared communications surface', (personaKey) => {
    const { container } = renderPersonaDashboard(personaKey);
    const text = normalizedText(container);

    expect(text).toMatch(/communication|message|inbox|announcement/i);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s renders page-level data truth status', (personaKey) => {
    const { container } = renderPersonaDashboard(personaKey);
    const text = normalizedText(container);

    expect(text).toMatch(/source|sync|last synced|data|live|fallback|demo|unavailable/i);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s does not render the generic BASE_NOTE sandbox copy', (personaKey) => {
    const { container } = renderPersonaDashboard(personaKey);
    const text = normalizedText(container);

    expect(text).not.toContain(BASE_NOTE);
    expect(text).not.toMatch(/Sandbox preview data shown\. Connect backend for live records\./i);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s has role-specific metrics with labels and values', (personaKey) => {
    const config = DASHBOARD_TEMPLATE_MAP[personaKey];

    expect(Array.isArray(config.metrics)).toBe(true);
    expect(config.metrics.length).toBeGreaterThan(0);

    const invalidMetrics = config.metrics.filter((metric) => {
      return !metric
        || typeof metric.label !== 'string'
        || metric.label.trim().length === 0
        || typeof metric.value !== 'string'
        || metric.value.trim().length === 0;
    });

    expect(invalidMetrics).toEqual([]);
  });

  it.each(PRODUCTION_PERSONA_KEYS)('%s has a stable dashboard identity', (personaKey) => {
    const config = DASHBOARD_TEMPLATE_MAP[personaKey];

    expect(typeof config.key).toBe('string');
    expect(config.key.length).toBeGreaterThan(0);
    expect(typeof config.activePath).toBe('string');
    expect(config.activePath.startsWith('/')).toBe(true);
    expect(typeof config.title).toBe('string');
    expect(config.title.length).toBeGreaterThan(0);
  });
});
