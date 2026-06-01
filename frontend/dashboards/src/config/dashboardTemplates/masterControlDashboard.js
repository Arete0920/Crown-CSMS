import { LIVE_NOTE } from './_baseData.js';

const DASH_TREND = [
  { month: 'Aug', value: 8 }, { month: 'Sep', value: 12 }, { month: 'Oct', value: 18 },
  { month: 'Nov', value: 22 }, { month: 'Dec', value: 28 }, { month: 'Jan', value: 32 },
  { month: 'Feb', value: 37 }, { month: 'Mar', value: 42 },
];
const UPTIME_TREND = [
  { month: 'Aug', value: 99.2 }, { month: 'Sep', value: 99.5 }, { month: 'Oct', value: 99.1 },
  { month: 'Nov', value: 99.7 }, { month: 'Dec', value: 99.8 }, { month: 'Jan', value: 99.6 },
  { month: 'Feb', value: 99.9 }, { month: 'Mar', value: 99.9 },
];

export default {
  key: 'masterControl',
  activePath: '/master-control-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'MC', name: 'Master Control', role: 'Platform â€” System Oversight & Operations' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Master Control!',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/masterControl/summary/',
  liveDataKey: 'masterControl',

  metrics: [
    { label: 'Active Dashboards', value: '42', detail: 'All 42 CROWN dashboards operational this session.', accent: 'emerald' },
    { label: 'System Health', value: '99.9%', detail: 'All services nominal â€” zero critical alerts.', accent: 'blue' },
    { label: 'Users Online', value: '87', detail: 'Current active sessions across all roles.', accent: 'gold' },
    { label: 'Support Tickets', value: '3', detail: '2 low priority, 1 medium â€” all assigned.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Review 3 open support tickets', detail: '1 medium priority â€” IT reviewing access issue.', state: 'Today', tone: 'warn' },
    { title: 'Confirm role assignments for new staff', detail: '4 new hires pending dashboard access setup.', state: 'This week', tone: 'warn' },
    { title: 'Review dashboard certification queue', detail: '6 dashboards pending final certification review.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Control room priorities',

  alerts: [
    { title: '4 new staff pending role assignment', detail: 'Dashboard access setup required before May 1.', tone: 'warn' },
    { title: '6 dashboards in certification queue', detail: 'Final certification review needed this week.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'platformHealth', icon: 'PH', title: 'Platform Health', status: 'All Systems Go', statusTone: 'good',
      mainKpi: '99.9% uptime â€” all 42 dashboards active', summary: 'All services nominal â€” zero critical alerts.',
      kpis: [{ label: 'Uptime', value: '99.9%' }, { label: 'Active Dashboards', value: '42' }, { label: 'Critical Alerts', value: '0' }, { label: 'Last Incident', value: '18 days ago' }],
      details: ['All 42 CROWN dashboards operational', 'Zero critical alerts in last 18 days', 'API response time avg 142ms', 'CDN cache hit rate 94%'],
      primaryActionLabel: 'System Status', backActionLabel: 'Reliability Dashboard',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:00 AM' },
    { key: 'userAccess', icon: 'UA', title: 'User Access', status: 'Watch', statusTone: 'warn',
      mainKpi: '87 active users â€” 4 pending setup', summary: '4 new staff need role assignment before May 1.',
      kpis: [{ label: 'Active Users', value: '87' }, { label: 'Pending Setup', value: '4' }, { label: 'Roles Assigned', value: '83' }, { label: 'Access Issues', value: '1' }],
      details: ['87 staff with active dashboard access', '4 new hires pending role assignment', '1 access issue in support queue', 'Last access audit: April 20'],
      primaryActionLabel: 'Manage Users', backActionLabel: 'IT Support',
      primaryActionHref: '/it-support-dashboard', backActionHref: '/it-support-dashboard', lastUpdated: '8:05 AM' },
    { key: 'tickets', icon: 'TK', title: 'Support Tickets', status: 'Stable', statusTone: 'good',
      mainKpi: '3 open tickets', summary: '2 low, 1 medium â€” all assigned and in progress.',
      kpis: [{ label: 'Open', value: '3' }, { label: 'Medium', value: '1' }, { label: 'Low', value: '2' }, { label: 'Resolved Today', value: '1' }],
      details: ['1 medium priority: dashboard access blocked', '2 low priority: display formatting', '1 ticket resolved earlier today', 'Avg resolution time: 4.2 hours'],
      primaryActionLabel: 'View Tickets', backActionLabel: 'IT Support',
      primaryActionHref: '/it-support-dashboard', backActionHref: '/it-support-dashboard', lastUpdated: '8:10 AM' },
    { key: 'certification', icon: 'CE', title: 'Dashboard Certification', status: 'In Progress', statusTone: 'warn',
      mainKpi: '6 dashboards in certification queue', summary: 'Final certification review needed this week.',
      kpis: [{ label: 'In Queue', value: '6' }, { label: 'Certified', value: '36' }, { label: 'Total', value: '42' }, { label: 'Completion', value: '86%' }],
      details: ['36 dashboards certified for production', '6 remaining in review queue', 'Certification completes gold standard validation', 'Target: 100% certified by May 15'],
      primaryActionLabel: 'Open Certification', backActionLabel: 'Cert Center',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:15 AM' },
    { key: 'releases', icon: 'RL', title: 'Release Management', status: 'Stable', statusTone: 'good',
      mainKpi: '3 releases this month', summary: 'All deployments successful â€” no rollbacks.',
      kpis: [{ label: 'Releases', value: '3' }, { label: 'Successful', value: '3' }, { label: 'Rollbacks', value: '0' }, { label: 'Next Deploy', value: 'TBD' }],
      details: ['3 successful deployments this month', 'Zero rollbacks â€” clean release record', 'Next deployment pending approval', 'Change window: Thursday 10 PM'],
      primaryActionLabel: 'View Releases', backActionLabel: 'Release Reliability',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:20 AM' },
    { key: 'compliance', icon: 'CO', title: 'Compliance & Audit', status: 'Stable', statusTone: 'good',
      mainKpi: 'No compliance flags', summary: 'All access logs current â€” audit trail maintained.',
      kpis: [{ label: 'Flags', value: '0' }, { label: 'Audit Trail', value: 'Current' }, { label: 'Last Audit', value: 'April 1' }, { label: 'Next Audit', value: 'July 1' }],
      details: ['No compliance flags in current period', 'Access logs exported weekly', 'Last audit: April 1 â€” all clear', 'Next scheduled audit: July 1, 2026'],
      primaryActionLabel: 'View Compliance', backActionLabel: 'Audit Dashboard',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Dashboard deployment', title: 'Dashboards Activated Over Time', chip: '42 active now', trend: DASH_TREND },
    { kicker: 'Platform reliability', title: 'System Uptime (%)', chip: '99.9% YTD', trend: UPTIME_TREND },
  ],

  activities: [
    'Medium priority ticket: dashboard access issue assigned to IT.',
    '4 new staff role assignments queued for setup.',
    '6 dashboards in certification queue â€” review this week.',
    '3rd successful deployment of month confirmed.',
    'Access audit log exported and archived.',
  ],

  quickActions: [
    { label: 'System Status', href: '/release-reliability-dashboard' },
    { label: 'Manage Access', href: '/it-support-dashboard' },
    { label: 'Support Tickets', href: '/it-support-dashboard' },
    { label: 'Certification', href: '/dashboard-certification-center' },
  ],

  statuses: [
    { label: 'Platform', state: 'All systems go' },
    { label: 'User Access', state: '4 pending setup' },
    { label: 'Support Queue', state: '3 open tickets' },
    { label: 'Certification', state: '86% complete' },
  ],
};
