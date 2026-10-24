import { describe, expect, it } from 'vitest';
import complianceAuditDashboard from './dashboardTemplates/complianceAuditDashboard.js';

describe('Heritage compliance demonstration disclosures', () => {
  it('identifies all configured claims as fictional rather than SOC 2 assurance', () => {
    const template = complianceAuditDashboard;
    const text = JSON.stringify(template);

    expect(template.dataState).toBe('fallback');
    expect(template.dataSource).toBe('live_api');
    expect(template.sourceLabel).toMatch(/fictional/i);
    expect(template.note).toMatch(/no SOC 2 Type I or Type II report/i);
    expect(template.statuses).toEqual(expect.arrayContaining([
      expect.objectContaining({ label: 'CROWN SOC 2 Report', state: 'Not issued or verified' }),
    ]));

    for (const unsupported of [
      /SOC2 Type II in progress/i,
      /SOC2 Type II fieldwork confirmed/i,
      /all three auditors confirmed/i,
      /86 of 100 active controls passing/i,
      /42 active organizational policies/i,
    ]) {
      expect(text).not.toMatch(unsupported);
    }

    for (const module of template.commandModules) {
      expect(module.status).toBe('Sample');
      expect(module.summary).toMatch(/illustrative|fictional|no actual|no live|sample/i);
    }
  });
});
