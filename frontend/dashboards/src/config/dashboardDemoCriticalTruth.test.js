import { describe, expect, it } from 'vitest';
import { DASHBOARD_DATA_REGISTRY, DEMO_CRITICAL_DASHBOARD_KEYS } from './dashboardDataRegistry.js';

const EXPECTED_DEMO_CRITICAL_KEYS = [
  'school-administrator',
  'admissions',
  'registrar',
  'billing',
  'financial-aid',
  'attendance',
  'gradebook',
  'communications',
  'scheduling',
  'parent',
  'teacher',
  'student',
  'dashboard-certification-center',
  'release-reliability',
  'compliance-audit',
];

const ALLOWED_DISCLOSED_FALLBACK_STATES = ['fallback', 'sample'];

describe('demo-critical dashboard data truth contract', () => {
  it('pins the sandbox/demo critical dashboard set explicitly', () => {
    expect(DEMO_CRITICAL_DASHBOARD_KEYS).toEqual(EXPECTED_DEMO_CRITICAL_KEYS);
  });

  it.each(EXPECTED_DEMO_CRITICAL_KEYS)(
    '%s has a summary endpoint and a disclosed non-live fallback state',
    (dashboardKey) => {
      const config = DASHBOARD_DATA_REGISTRY[dashboardKey];

      expect(config).toBeTruthy();
      expect(config.endpoint).toBe(`/api/v1/dashboards/${dashboardKey}/summary`);
      expect(config.allowScaffoldFallback).toBe(true);
      expect(config.fallbackData).toBeTruthy();
      expect(config.fallbackData.dashboard_key).toBe(dashboardKey);
      expect(Array.isArray(config.fallbackData.metrics)).toBe(true);
      expect(config.fallbackData.metrics.length).toBeGreaterThan(0);
      expect(Array.isArray(config.fallbackData.alerts)).toBe(true);
      expect(config.fallbackData.alerts.length).toBeGreaterThan(0);
      expect(Array.isArray(config.fallbackData.queue)).toBe(true);
      expect(config.fallbackData.queue.length).toBeGreaterThan(0);
      expect(ALLOWED_DISCLOSED_FALLBACK_STATES).toContain(config.fallbackData.meta?.served_from);
      expect(config.fallbackData.meta?.live_certified).toBe(false);
      expect(config.fallbackData.meta?.sandbox_demo_only).toBe(true);
    },
  );
});
