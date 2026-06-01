import { LIVE_NOTE } from './_baseData.js';

const DEPLOY_TREND = [
  { month: 'Aug', value: 4 }, { month: 'Sep', value: 6 }, { month: 'Oct', value: 8 },
  { month: 'Nov', value: 7 }, { month: 'Dec', value: 9 }, { month: 'Jan', value: 11 },
  { month: 'Feb', value: 12 }, { month: 'Mar', value: 14 },
];
const UPTIME_TREND = [
  { month: 'Aug', value: 99.1 }, { month: 'Sep', value: 99.3 }, { month: 'Oct', value: 99.5 },
  { month: 'Nov', value: 99.4 }, { month: 'Dec', value: 99.6 }, { month: 'Jan', value: 99.7 },
  { month: 'Feb', value: 99.8 }, { month: 'Mar', value: 99.9 },
];

export default {
  key: 'releaseReliability',
  activePath: '/release-reliability-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'RR', name: 'Release & Reliability', role: 'Platform â€” Release Engineering & Site Reliability' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Release Team!',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/releaseReliability/summary/',
  liveDataKey: 'releaseReliability',

  metrics: [
    { label: 'Deployments (March)', value: '14', detail: '14 production deployments â€” all successful.', accent: 'emerald' },
    { label: 'Uptime (30-day)', value: '99.9%', detail: 'Platform SLA target 99.8% â€” exceeded.', accent: 'blue' },
    { label: 'Incidents (Month)', value: '1', detail: '1 P2 incident â€” 22-minute resolution.', accent: 'gold' },
    { label: 'MTTR', value: '22 min', detail: 'Mean time to resolution â€” best month this year.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Complete post-mortem for April 8 P2 incident', detail: 'Database connection pool exhaustion â€” postmortem due April 14.', state: 'Today', tone: 'warn' },
    { title: 'Deploy v4.2.1 hotfix to production', detail: 'Approved hotfix â€” stage verified, production deploy tonight.', state: 'Today', tone: 'nominal' },
    { title: 'Q2 reliability review with engineering leads', detail: 'Quarterly SLA review and Q3 reliability planning.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Release priorities',

  alerts: [
    { title: 'Post-mortem for April 8 P2 due April 14', detail: 'Root cause identified â€” document and action items needed.', tone: 'warn' },
    { title: 'v4.2.1 hotfix cleared for production deploy', detail: 'Staging verified â€” deploy tonight in maintenance window.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'deployments', icon: 'DP', title: 'Deployments', status: 'Healthy', statusTone: 'good',
      mainKpi: '14 deployments in March â€” all success', summary: 'Zero failed deployments â€” best deployment velocity this year.',
      kpis: [{ label: 'March Deploys', value: '14' }, { label: 'Success', value: '14' }, { label: 'Rollbacks', value: '0' }, { label: 'YTD Total', value: '68' }],
      details: ['14 production deployments in March', 'Zero failed or rolled-back deployments', '68 total deployments YTD', 'v4.2.1 hotfix ready for tonight'],
      primaryActionLabel: 'Deployment Log', backActionLabel: 'Release Calendar',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:00 AM' },
    { key: 'uptime', icon: 'UT', title: 'Uptime', status: 'SLA Exceeded', statusTone: 'good',
      mainKpi: '99.9% uptime â€” SLA target 99.8%', summary: 'Consistently exceeding SLA commitments.',
      kpis: [{ label: '30-Day Uptime', value: '99.9%' }, { label: 'SLA Target', value: '99.8%' }, { label: 'Downtime (month)', value: '26 min' }, { label: 'YTD Uptime', value: '99.7%' }],
      details: ['99.9% uptime in March â€” best month this year', 'SLA target 99.8% â€” exceeded by 0.1%', 'Total downtime: 26 minutes in March (P2 incident)', 'YTD average: 99.7%'],
      primaryActionLabel: 'Uptime Report', backActionLabel: 'SLA Details',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:05 AM' },
    { key: 'incidents', icon: 'IN', title: 'Incidents', status: 'Resolved', statusTone: 'good',
      mainKpi: '1 P2 incident in March â€” 22 min MTTR', summary: 'Database connection pool issue â€” resolved, postmortem pending.',
      kpis: [{ label: 'March Incidents', value: '1' }, { label: 'Severity', value: 'P2' }, { label: 'MTTR', value: '22 min' }, { label: 'Postmortem', value: 'Due Apr 14' }],
      details: ['1 P2 incident: April 8, 2:14 AM', 'Root cause: database connection pool exhaustion', 'Resolved in 22 minutes â€” MTTR target 30 min', 'Postmortem document due April 14'],
      primaryActionLabel: 'Incident Report', backActionLabel: 'Postmortem',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:10 AM' },
    { key: 'hotfix', icon: 'HF', title: 'v4.2.1 Hotfix', status: 'Ready to Deploy', statusTone: 'good',
      mainKpi: 'Deploy tonight â€” staging verified', summary: 'Connection pool limit increase â€” zero risk change.',
      kpis: [{ label: 'Version', value: 'v4.2.1' }, { label: 'Staging', value: 'Verified' }, { label: 'Deploy Time', value: 'Tonight' }, { label: 'Impact', value: 'Zero downtime' }],
      details: ['v4.2.1: connection pool max increased to 250', 'Staging environment verified â€” no regressions', 'Zero-downtime rolling deploy', 'Deploy window: 11 PM tonight'],
      primaryActionLabel: 'Deploy v4.2.1', backActionLabel: 'Release Notes',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:15 AM' },
    { key: 'sla', icon: 'SL', title: 'SLA Metrics', status: 'Met', statusTone: 'good',
      mainKpi: 'All SLAs met â€” school commitments fulfilled', summary: 'Q1 SLA report ready â€” all commitments met.',
      kpis: [{ label: 'Uptime SLA', value: 'Met' }, { label: 'Response Time', value: 'Met' }, { label: 'Support SLA', value: 'Met' }, { label: 'Q1 Report', value: 'Ready' }],
      details: ['Uptime SLA 99.8%: met at 99.9%', 'P95 response time SLA 500ms: met at 248ms', 'Support SLA 4-hour response: met at 2.8 hrs avg', 'Q1 SLA report ready for distribution'],
      primaryActionLabel: 'SLA Report', backActionLabel: 'Commitments',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:20 AM' },
    { key: 'oncall', icon: 'OC', title: 'On-Call', status: 'Assigned', statusTone: 'good',
      mainKpi: 'On-call rotation current', summary: 'Full rotation assigned â€” escalation paths clear.',
      kpis: [{ label: 'Primary On-Call', value: 'Assigned' }, { label: 'Secondary', value: 'Assigned' }, { label: 'Rotation', value: 'Weekly' }, { label: 'PagerDuty', value: 'Active' }],
      details: ['Weekly on-call rotation active', 'Primary and secondary engineers assigned', 'PagerDuty escalation configured', 'No on-call incidents this rotation'],
      primaryActionLabel: 'On-Call Schedule', backActionLabel: 'Escalation',
      primaryActionHref: '/release-reliability-dashboard', backActionHref: '/release-reliability-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Deployment cadence', title: 'Production Deployments Per Month', chip: '14 in March', trend: DEPLOY_TREND },
    { kicker: 'Platform reliability', title: 'Monthly Uptime (%)', chip: '99.9% (March)', trend: UPTIME_TREND },
  ],

  activities: [
    'v4.2.1 hotfix approved â€” production deploy scheduled tonight.',
    'April 8 P2 postmortem in progress â€” due April 14.',
    '14 successful deployments in March â€” zero rollbacks.',
    '99.9% uptime â€” SLA target exceeded for 3rd consecutive month.',
    'Q2 reliability review with engineering leads scheduled.',
  ],

  quickActions: [
    { label: 'Deployment Log', href: '/release-reliability-dashboard' },
    { label: 'Incident Report', href: '/release-reliability-dashboard' },
    { label: 'SLA Report', href: '/release-reliability-dashboard' },
    { label: 'On-Call Schedule', href: '/release-reliability-dashboard' },
  ],

  statuses: [
    { label: 'Uptime (30d)', state: '99.9%' },
    { label: 'Deployments', state: '14 (all success)' },
    { label: 'Incidents', state: '1 (P2, resolved)' },
    { label: 'MTTR', state: '22 min' },
  ],
};
