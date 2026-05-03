import { BASE_NOTE } from './_baseData.js';

const API_TREND = [
  { month: 'Aug', value: 98.2 }, { month: 'Sep', value: 98.8 }, { month: 'Oct', value: 99.1 },
  { month: 'Nov', value: 99.3 }, { month: 'Dec', value: 99.0 }, { month: 'Jan', value: 99.4 },
  { month: 'Feb', value: 99.6 }, { month: 'Mar', value: 99.7 },
];
const AUTO_TREND = [
  { month: 'Aug', value: 14 }, { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 },
  { month: 'Nov', value: 26 }, { month: 'Dec', value: 28 }, { month: 'Jan', value: 32 },
  { month: 'Feb', value: 36 }, { month: 'Mar', value: 41 },
];

export default {
  key: 'integrationsAutomation',
  activePath: '/integrations-automation-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'IA', name: 'Integrations & Automation', role: 'Platform — System Integrations & Process Automation' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Integrations Team!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Active Integrations', value: '28', detail: '28 live integrations — SIS, LMS, Finance, SSO.', accent: 'blue' },
    { label: 'API Health', value: '99.7%', detail: '30-day uptime across all integration endpoints.', accent: 'emerald' },
    { label: 'Automations Running', value: '41', detail: '41 active automation workflows this month.', accent: 'gold' },
    { label: 'Sync Errors', value: '2', detail: '2 sync errors in last 24h — both non-critical.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Resolve 2 open sync errors', detail: 'Attendance sync and finance reconciliation — non-critical but review today.', state: 'Today', tone: 'warn' },
    { title: 'Deploy new LMS integration for Covenant', detail: 'Canvas LMS connector ready for Covenant school go-live.', state: 'This week', tone: 'nominal' },
    { title: 'Audit stale automation workflows', detail: '6 automations inactive >90 days — review and archive.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Integrations priorities',

  alerts: [
    { title: '2 sync errors in last 24 hours', detail: 'Attendance and finance sync — non-critical but review today.', tone: 'warn' },
    { title: '6 automations inactive >90 days', detail: 'Stale workflows should be reviewed and archived.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'integrations', icon: 'IN', title: 'Integrations', status: 'Healthy', statusTone: 'good',
      mainKpi: '28 active — 99.7% uptime', summary: 'All major integrations healthy.',
      kpis: [{ label: 'Active', value: '28' }, { label: 'Uptime', value: '99.7%' }, { label: 'Errors (24h)', value: '2' }, { label: 'Pending', value: '3' }],
      details: ['28 live integrations across all systems', 'SIS connector: nominal', 'LMS connectors: 4 active, 1 pending', 'Finance and payroll: nominal'],
      primaryActionLabel: 'Integration Status', backActionLabel: 'Error Log',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/integrations-automation-dashboard', lastUpdated: '8:00 AM' },
    { key: 'api', icon: 'AP', title: 'API Health', status: 'Healthy', statusTone: 'good',
      mainKpi: '99.7% — 30-day API uptime', summary: 'All API endpoints healthy — no critical issues.',
      kpis: [{ label: 'Uptime', value: '99.7%' }, { label: 'Endpoints', value: '84' }, { label: 'Healthy', value: '82' }, { label: 'Degraded', value: '2' }],
      details: ['84 active API endpoints', '82 fully healthy — 2 minor latency issues', '30-day uptime: 99.7%', 'P95 response time: 248ms'],
      primaryActionLabel: 'API Monitor', backActionLabel: 'Endpoint List',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/integrations-automation-dashboard', lastUpdated: '8:05 AM' },
    { key: 'automations', icon: 'AU', title: 'Automations', status: 'Active', statusTone: 'good',
      mainKpi: '41 workflows running', summary: 'Automations processing normally — 6 stale for review.',
      kpis: [{ label: 'Active', value: '41' }, { label: 'Stale', value: '6' }, { label: 'Monthly Runs', value: '12,400' }, { label: 'Success Rate', value: '99.6%' }],
      details: ['41 automation workflows active', '12,400 automation runs this month', '99.6% success rate', '6 workflows inactive >90 days — review'],
      primaryActionLabel: 'Automation Manager', backActionLabel: 'Stale Review',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/integrations-automation-dashboard', lastUpdated: '8:10 AM' },
    { key: 'errors', icon: 'ER', title: 'Sync Errors', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 errors (24h) — non-critical', summary: 'Attendance and finance sync errors need same-day review.',
      kpis: [{ label: 'Errors (24h)', value: '2' }, { label: 'Type', value: 'Non-critical' }, { label: 'Oldest', value: '18 hrs' }, { label: 'Auto-retry', value: 'Active' }],
      details: ['Error 1: Attendance sync timeout — retrying', 'Error 2: Finance reconciliation mismatch — needs manual review', 'Auto-retry active for both errors', 'No data loss — reconciliation required'],
      primaryActionLabel: 'Error Log', backActionLabel: 'Resolve',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/integrations-automation-dashboard', lastUpdated: '8:15 AM' },
    { key: 'newIntegrations', icon: 'NI', title: 'New Integrations', status: 'In Progress', statusTone: 'good',
      mainKpi: '3 integrations in build pipeline', summary: 'Canvas LMS for Covenant ready to deploy.',
      kpis: [{ label: 'In Pipeline', value: '3' }, { label: 'Canvas LMS', value: 'Ready' }, { label: 'Payroll v2', value: 'Testing' }, { label: 'SSO Expand', value: 'Dev' }],
      details: ['Canvas LMS connector: ready for Covenant deployment', 'Payroll v2 API: in testing — 2 bugs open', 'SSO expansion to 5 new schools: in development', 'Target deployments: May 1'],
      primaryActionLabel: 'Deployment Plan', backActionLabel: 'Build Status',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/integrations-automation-dashboard', lastUpdated: '8:20 AM' },
    { key: 'monitoring', icon: 'MN', title: 'Monitoring', status: 'Active', statusTone: 'good',
      mainKpi: 'All monitors active — 2 alerts', summary: 'Platform-wide monitoring healthy — 2 minor alerts.',
      kpis: [{ label: 'Monitors', value: '64' }, { label: 'Active', value: '64' }, { label: 'Alerts', value: '2' }, { label: 'On-Call', value: 'Assigned' }],
      details: ['64 monitoring checks active', '2 non-critical alerts — under review', 'On-call rotation assigned for week', 'Weekly health summary ready'],
      primaryActionLabel: 'Monitoring Dashboard', backActionLabel: 'Alert History',
      primaryActionHref: '/integrations-automation-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'API reliability', title: 'API Health Uptime (%)', chip: '99.7% (30-day)', trend: API_TREND },
    { kicker: 'Automation growth', title: 'Active Automation Workflows', chip: '41 active', trend: AUTO_TREND },
  ],

  activities: [
    '2 sync errors flagged — attendance and finance, non-critical.',
    'Canvas LMS connector ready for Covenant school go-live.',
    '6 stale automation workflows queued for review and archive.',
    '41 automations ran 12,400 workflows this month at 99.6% success.',
    'API uptime at 99.7% — program-best 30-day performance.',
  ],

  quickActions: [
    { label: 'Integration Status', href: '/integrations-automation-dashboard' },
    { label: 'Error Log', href: '/integrations-automation-dashboard' },
    { label: 'Automations', href: '/integrations-automation-dashboard' },
    { label: 'API Monitor', href: '/integrations-automation-dashboard' },
  ],

  statuses: [
    { label: 'API Health', state: '99.7% uptime' },
    { label: 'Sync Errors', state: '2 non-critical' },
    { label: 'Automations', state: '41 active' },
    { label: 'New Integrations', state: '3 in pipeline' },
  ],
};
