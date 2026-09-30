import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import useDashboardData from '../hooks/useDashboardData.js';

function cloneConfig(template) {
  if (typeof globalThis.structuredClone === 'function') {
    return globalThis.structuredClone(template);
  }
  return JSON.parse(JSON.stringify(template));
}

function percent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${Math.round(n)}%` : '--';
}

export default function MarketingDashboard() {
  const baseConfig = getDashboardTemplate('marketing');
  const dashboard = useDashboardData('marketing');
  const payload = dashboard.data || {};
  const isLive = dashboard.source === 'live' && !dashboard.error;
  const dataState = isLive ? 'live' : dashboard.loading ? 'loading' : dashboard.error ? 'unavailable' : 'fallback';
  const sourceLabel = isLive
    ? 'Tenant-scoped admissions and marketing attribution data'
    : dashboard.loading
      ? 'Marketing data loading'
      : dashboard.error
        ? 'Marketing data unavailable'
        : 'Marketing configuration fallback';

  const inquiries = Number(payload.inquiries || 0);
  const tours = Number(payload.tours_scheduled || 0);
  const applications = Number(payload.applications || 0);
  const enrolled = Number(payload.enrolled || 0);
  const stalled = Number(payload.stalled_leads || 0);
  const conversion = Number(payload.overall_application_to_enrollment_pct);
  const sources = Array.isArray(payload.source_attribution) ? payload.source_attribution : [];
  const actions = Array.isArray(payload.action_queue) ? payload.action_queue : [];
  const marketConfigured = payload.market_intelligence?.status !== 'not_configured';
  const advertisingConfigured = payload.advertising?.status !== 'not_configured';

  const config = cloneConfig(baseConfig);
  config.disableLiveData = true;
  config.dataState = dataState;
  config.sourceLabel = sourceLabel;
  config.lastSyncLabel = isLive ? 'Last synced just now' : sourceLabel;
  config.note = isLive
    ? 'Marketing Command is operating from current tenant-scoped admissions truth.'
    : 'Marketing Command is waiting for verified live data.';

  config.metrics = [
    { label: 'Inquiries', value: String(inquiries), detail: 'Prospective-family inquiry records.', accent: 'blue', dataState, sourceLabel },
    { label: 'Tours Scheduled', value: String(tours), detail: 'Families with a scheduled tour event.', accent: 'gold', dataState, sourceLabel },
    { label: 'Applications', value: String(applications), detail: 'Non-draft applications in the active tenant.', accent: 'navy', dataState, sourceLabel },
    { label: 'Stalled Prospects', value: String(stalled), detail: 'Open records with no movement for more than seven days.', accent: stalled > 0 ? 'gold' : 'emerald', dataState, sourceLabel },
  ];

  config.priorities = actions.length > 0
    ? actions.map((item) => ({
        title: item.title,
        detail: item.detail,
        state: item.state || 'Ready',
        tone: item.priority === 'high' ? 'warn' : 'good',
      }))
    : [{
        title: 'No urgent marketing follow-up detected',
        detail: 'Continue monitoring inquiry progression and source performance.',
        state: 'Stable',
        tone: 'good',
      }];

  config.alerts = [
    {
      title: marketConfigured ? 'Market intelligence configured' : 'Market intelligence not configured',
      detail: marketConfigured
        ? 'External demographic and market-opportunity inputs are available.'
        : payload.market_intelligence?.message || 'Connect approved demographic and market datasets before presenting opportunity estimates.',
      tone: marketConfigured ? 'good' : 'warn',
    },
    {
      title: advertisingConfigured ? 'Advertising attribution configured' : 'Advertising spend attribution not configured',
      detail: advertisingConfigured
        ? 'Campaign spend and outcome attribution are available.'
        : payload.advertising?.message || 'Connect approved campaign cost data before calculating advertising ROI.',
      tone: advertisingConfigured ? 'good' : 'warn',
    },
  ];

  config.commandModules = [
    {
      key: 'funnel',
      icon: 'FN',
      title: 'Enrollment Funnel',
      status: stalled > 0 ? 'Watch' : 'Stable',
      statusTone: stalled > 0 ? 'warn' : 'good',
      mainKpi: `${inquiries} → ${tours} → ${applications} → ${enrolled}`,
      summary: `Application-to-enrollment conversion: ${percent(conversion)}`,
      kpis: [
        { label: 'Inquiries', value: String(inquiries) },
        { label: 'Tours', value: String(tours) },
        { label: 'Applications', value: String(applications) },
        { label: 'Enrolled', value: String(enrolled) },
      ],
      details: [
        `Stalled prospects: ${stalled}`,
        `Application-to-enrollment: ${percent(conversion)}`,
        'Admissions remains the canonical enrollment workflow.',
      ],
      dataState,
      sourceLabel,
      primaryActionLabel: 'Open Admissions',
      backActionLabel: 'View Pipeline',
      primaryActionHref: '/admissions',
      backActionHref: '/admissions/pipeline',
      lastUpdated: isLive ? 'Live' : 'Unavailable',
    },
    {
      key: 'sources',
      icon: 'SR',
      title: 'Source Attribution',
      status: sources.length > 0 ? 'Stable' : 'Watch',
      statusTone: sources.length > 0 ? 'good' : 'warn',
      mainKpi: sources.length > 0 ? `${sources.length} tracked source(s)` : 'No source attribution yet',
      summary: sources[0]
        ? `${sources[0].source}: ${sources[0].applications} applications / ${sources[0].enrolled} enrolled`
        : 'Capture source consistently at inquiry/application intake.',
      kpis: sources.slice(0, 4).map((row) => ({
        label: row.source,
        value: String(row.applications),
      })),
      details: sources.slice(0, 5).map(
        (row) => `${row.source}: ${row.applications} applications · ${row.enrolled} enrolled · ${percent(row.conversion_pct)} conversion`
      ),
      dataState,
      sourceLabel,
      primaryActionLabel: 'Review Admissions Sources',
      backActionLabel: 'Marketing Command',
      primaryActionHref: '/admissions/pipeline',
      backActionHref: '/marketing',
      lastUpdated: isLive ? 'Live' : 'Unavailable',
    },
    {
      key: 'market',
      icon: 'MI',
      title: 'Market Intelligence',
      status: marketConfigured ? 'Stable' : 'Not Configured',
      statusTone: marketConfigured ? 'good' : 'warn',
      mainKpi: marketConfigured ? 'Market data connected' : 'External market data required',
      summary: payload.market_intelligence?.message || 'Demographics, drive-time, church, preschool, and competitor data are not connected.',
      kpis: [
        { label: 'Demographics', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Drive-time', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Church/feeder', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Competitors', value: marketConfigured ? 'Ready' : '--' },
      ],
      details: [
        'Designed for addressable-family, market-penetration, feeder, and geographic opportunity analysis.',
        'No estimates are shown until verified external data are connected.',
      ],
      dataState: marketConfigured ? dataState : 'unavailable',
      sourceLabel: marketConfigured ? sourceLabel : 'External market datasets not configured',
      primaryActionLabel: 'Marketing Command',
      backActionLabel: 'Admissions',
      primaryActionHref: '/marketing',
      backActionHref: '/admissions',
      lastUpdated: marketConfigured ? 'Configured' : 'Pending integration',
    },
    {
      key: 'advertising',
      icon: 'AD',
      title: 'Advertising ROI',
      status: advertisingConfigured ? 'Stable' : 'Not Configured',
      statusTone: advertisingConfigured ? 'good' : 'warn',
      mainKpi: advertisingConfigured ? 'Campaign attribution connected' : 'Spend data required',
      summary: payload.advertising?.message || 'Advertising ROI requires verified spend and campaign-attribution data.',
      kpis: [
        { label: 'Spend', value: '--' },
        { label: 'Cost / inquiry', value: '--' },
        { label: 'Cost / application', value: '--' },
        { label: 'Cost / enrollment', value: '--' },
      ],
      details: [
        'Will connect campaign spend to inquiry, application, and enrollment outcomes.',
        'Crown will not calculate ROI from unverified or manually assumed spend.',
      ],
      dataState: advertisingConfigured ? dataState : 'unavailable',
      sourceLabel: advertisingConfigured ? sourceLabel : 'Advertising data not configured',
      primaryActionLabel: 'Marketing Command',
      backActionLabel: 'Reports',
      primaryActionHref: '/marketing',
      backActionHref: '/reports',
      lastUpdated: advertisingConfigured ? 'Configured' : 'Pending integration',
    },
  ];

  config.trendPanels = [];
  config.activities = [
    `Tracked sources: ${sources.length}`,
    `Open stalled prospect records: ${stalled}`,
    marketConfigured ? 'Market intelligence data connected.' : 'Market intelligence integration pending.',
    advertisingConfigured ? 'Advertising attribution connected.' : 'Advertising attribution integration pending.',
  ];
  config.statuses = [
    { label: 'Marketing Data Source', state: sourceLabel },
    { label: 'Admissions Attribution', state: sources.length > 0 ? 'Active' : 'Needs source data' },
    { label: 'Market Intelligence', state: marketConfigured ? 'Configured' : 'Not configured' },
    { label: 'Advertising Attribution', state: advertisingConfigured ? 'Configured' : 'Not configured' },
  ];

  return <CrownDashboardTemplate config={config} roleKey="marketing" />;
}
