import { describe, expect, it } from 'vitest';
import {
  DASHBOARD_TEMPLATE_MAP,
  REQUIRED_DASHBOARD_TEMPLATE_SECTIONS,
  getDashboardTemplate,
} from './dashboardTemplates/index.js';

const TEMPLATE_KEYS = Object.keys(DASHBOARD_TEMPLATE_MAP);

function expectNonEmptyArray(value, label, templateKey) {
  expect(Array.isArray(value), `${templateKey} missing array ${label}`).toBe(true);
  expect(value.length, `${templateKey} has empty ${label}`).toBeGreaterThan(0);
}

function expectObject(value, label, templateKey) {
  expect(value && typeof value === 'object' && !Array.isArray(value), `${templateKey} missing object ${label}`).toBe(true);
}

function expectNonEmptyString(value, label, templateKey) {
  expect(typeof value, `${templateKey} missing string ${label}`).toBe('string');
  expect(value.trim().length, `${templateKey} has empty ${label}`).toBeGreaterThan(0);
}

describe('canonical CROWN dashboard template contract', () => {
  it('tracks the required shared section names as an explicit product contract', () => {
    expect(REQUIRED_DASHBOARD_TEMPLATE_SECTIONS).toEqual([
      'faithCommunity.devotion',
      'faithCommunity.prayerRequests',
      'faithCommunity.announcements',
      'faithCommunity.celebrations',
      'communications.inboxItems',
      'communications.announcementItems',
      'communications.urgentItems',
      'sourceSyncTruth.dataSource',
      'sourceSyncTruth.truthLabel',
      'sourceSyncTruth.lastSyncLabel',
      'metrics',
      'priorities',
      'alerts',
      'commandModules',
      'quickActions',
    ]);
  });

  it('covers the full dashboard template registry and required aliases', () => {
    expect(TEMPLATE_KEYS.length).toBeGreaterThanOrEqual(40);
    expect(TEMPLATE_KEYS).toEqual(expect.arrayContaining([
      'schoolBoard',
      'healthOffice',
      'foodService',
      'itSupport',
      'athleticsDirector',
      'chaplainSpiritualLife',
    ]));
  });

  it.each(TEMPLATE_KEYS)('%s exposes the shared CROWN dashboard sections', (templateKey) => {
    const template = getDashboardTemplate(templateKey);

    expectObject(template, 'template', templateKey);
    expectNonEmptyString(template.title, 'title', templateKey);

    expectObject(template.faithCommunity, 'faithCommunity', templateKey);
    expectObject(template.faithCommunity.devotion, 'faithCommunity.devotion', templateKey);
    expectNonEmptyArray(template.faithCommunity.prayerRequests, 'faithCommunity.prayerRequests', templateKey);
    expectNonEmptyArray(template.faithCommunity.announcements, 'faithCommunity.announcements', templateKey);
    expectNonEmptyArray(template.faithCommunity.celebrations, 'faithCommunity.celebrations', templateKey);

    expectObject(template.communications, 'communications', templateKey);
    expectNonEmptyArray(template.communications.inboxItems, 'communications.inboxItems', templateKey);
    expectNonEmptyArray(template.communications.announcementItems, 'communications.announcementItems', templateKey);
    expectNonEmptyArray(template.communications.urgentItems, 'communications.urgentItems', templateKey);

    expectObject(template.sourceSyncTruth, 'sourceSyncTruth', templateKey);
    expectNonEmptyString(template.sourceSyncTruth.dataSource, 'sourceSyncTruth.dataSource', templateKey);
    expectNonEmptyString(template.sourceSyncTruth.truthLabel, 'sourceSyncTruth.truthLabel', templateKey);
    expectNonEmptyString(template.sourceSyncTruth.lastSyncLabel, 'sourceSyncTruth.lastSyncLabel', templateKey);

    expectNonEmptyArray(template.metrics, 'metrics', templateKey);
    expect(Array.isArray(template.priorities), `${templateKey} missing priorities array`).toBe(true);
    expect(Array.isArray(template.alerts), `${templateKey} missing alerts array`).toBe(true);
    expect(Array.isArray(template.commandModules), `${templateKey} missing commandModules array`).toBe(true);
    expect(Array.isArray(template.quickActions), `${templateKey} missing quickActions array`).toBe(true);

    if (template.dataSource === 'live_api') {
      expectNonEmptyString(template.apiEndpoint, 'apiEndpoint', templateKey);
      expect(template.apiEndpoint.startsWith('/api/v1/'), `${templateKey} apiEndpoint must use /api/v1/`).toBe(true);
      expect(
        template.apiEndpoint.endsWith('/summary') || template.apiEndpoint.endsWith('/summary/'),
        `${templateKey} apiEndpoint must end in /summary`,
      ).toBe(true);
      expectNonEmptyString(template.liveDataKey, 'liveDataKey', templateKey);
      expect(template.sourceSyncTruth.liveDataKey, `${templateKey} sourceSyncTruth liveDataKey must match template liveDataKey`).toBe(template.liveDataKey);
    }
  });
});
