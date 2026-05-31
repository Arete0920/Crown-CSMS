import { BASE_NOTE } from './_baseData.js';

const UPTIME_TREND = [
  { month: 'Sep', value: 99.6 }, { month: 'Oct', value: 99.7 }, { month: 'Nov', value: 99.8 },
  { month: 'Dec', value: 99.7 }, { month: 'Jan', value: 99.9 }, { month: 'Feb', value: 99.8 }, { month: 'Mar', value: 99.8 },
];
const TICKET_TREND = [
  { month: 'Sep', value: 18 }, { month: 'Oct', value: 14 }, { month: 'Nov', value: 16 },
  { month: 'Dec', value: 11 }, { month: 'Jan', value: 13 }, { month: 'Feb', value: 9 }, { month: 'Mar', value: 12 },
];

export default {
  key: 'it',
  activePath: '/it',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'IT', name: 'IT Director', role: 'Technology â€” Infrastructure & Devices' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, IT Director!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'IT support widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until IT support metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/it/summary/',
  liveDataKey: 'it',
  metrics: [
    { label: 'Open Tickets', value: '12', detail: '5 urgent, 1 overdue >14 days.', accent: 'gold' },
    { label: 'System Uptime', value: '99.8%', detail: 'Rolling 30-day across all monitored services.', accent: 'emerald' },
    { label: 'Devices Compliant', value: '141 / 148', detail: '7 devices currently out of compliance.', accent: 'navy' },
    { label: 'SSL Cert Expiry', value: '42 days', detail: 'Renewal window opens in 2 weeks.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Resolve overdue ticket #4421', detail: 'Open >14 days â€” escalation policy triggered.', state: 'Today', tone: 'warn' },
    { title: 'Bring 7 devices back into compliance', detail: 'Run remediation playbook before Friday audit.', state: 'This week', tone: 'warn' },
    { title: 'Confirm SSL cert renewal vendor', detail: '42-day expiry window â€” order today to avoid lapse.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'IT priorities',

  alerts: [
    { title: 'Open ticket >14 days', detail: 'One support ticket exceeds 14-day SLA â€” owner reassignment recommended.', tone: 'warn' },
    { title: '7 devices non-compliant', detail: 'Devices missing latest security baseline â€” auto-remediation queue ready.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'tickets', icon: 'TK', title: 'Helpdesk Tickets', status: 'Watch', statusTone: 'warn',
      mainKpi: '12 open / 1 overdue', summary: 'Support volume normal; one ticket exceeds 14-day SLA.',
      kpis: [{ label: 'Open', value: '12' }, { label: 'Overdue', value: '1' }, { label: 'Resolved MTD', value: '47' }, { label: 'Avg time to close', value: '2.4 d' }],
      details: ['Ticket #4421 â€” overdue, owner reassignment needed', '5 tickets escalated to Tier 2', '47 tickets resolved this month', 'CSAT score 4.6/5 last survey'],
      primaryActionLabel: 'Open Ticket Queue', backActionLabel: 'Review SLA',
      primaryActionHref: '/it', backActionHref: '/it', lastUpdated: '8:35 AM' },
    { key: 'devices', icon: 'DV', title: 'Devices & Compliance', status: 'Watch', statusTone: 'warn',
      mainKpi: '141 / 148 compliant', summary: '95% device compliance â€” 7 devices out of policy.',
      kpis: [{ label: 'Total devices', value: '148' }, { label: 'Compliant', value: '141' }, { label: 'Non-compliant', value: '7' }, { label: 'Compliance rate', value: '95%' }],
      details: ['7 devices missing latest security baseline', 'Auto-remediation queued for 4 devices', '3 devices flagged for manual review', 'Asset registry total: 243'],
      primaryActionLabel: 'Open Device Inventory', backActionLabel: 'Run Remediation',
      primaryActionHref: '/it', backActionHref: '/it', lastUpdated: '8:20 AM' },
    { key: 'system', icon: 'SY', title: 'System Status', status: 'Stable', statusTone: 'good',
      mainKpi: 'API and DB up â€” 99.8% uptime', summary: 'All monitored services healthy. Last deploy clean.',
      kpis: [{ label: 'API status', value: 'OK' }, { label: 'DB status', value: 'OK' }, { label: '30-day uptime', value: '99.8%' }, { label: 'Last deploy', value: 'd196ab66' }],
      details: ['API responding within p95 latency target', 'Database replication lag <50ms', 'Last deploy tag: prod-deploy-2026-02-22-1415', 'No active outages or degraded services'],
      primaryActionLabel: 'Open System Status', backActionLabel: 'View Deploy Log',
      primaryActionHref: '/system-status', backActionHref: '/release-readiness', lastUpdated: '8:40 AM' },
    { key: 'security', icon: 'SE', title: 'Security & Certificates', status: 'Watch', statusTone: 'warn',
      mainKpi: 'SSL expires in 42 days', summary: 'Cert renewal window open â€” order this week.',
      kpis: [{ label: 'SSL expiry', value: '42 days' }, { label: 'Failed checks', value: '0' }, { label: 'MFA enrollment', value: '98%' }, { label: 'Active threats', value: '0' }],
      details: ['Primary cert renewal window now open', 'No failed security checks in last 30 days', '2 staff still pending MFA enrollment', 'Annual security review on track for May'],
      primaryActionLabel: 'Open Security Console', backActionLabel: 'Renew Certs',
      primaryActionHref: '/security', backActionHref: '/it', lastUpdated: '7:50 AM' },
    { key: 'assets', icon: 'AS', title: 'Asset Inventory', status: 'Stable', statusTone: 'good',
      mainKpi: '243 assets tracked', summary: 'All devices, licenses, and AV equipment in registry.',
      kpis: [{ label: 'Total assets', value: '243' }, { label: 'Devices', value: '148' }, { label: 'Licenses', value: '64' }, { label: 'AV equipment', value: '31' }],
      details: ['12 new devices imaged this month', '3 licenses up for renewal in Q3', 'AV equipment audit complete', 'Asset write-offs: 2 this quarter'],
      primaryActionLabel: 'Open Asset Registry', backActionLabel: 'Audit Log',
      primaryActionHref: '/it', backActionHref: '/it', lastUpdated: '7:30 AM' },
    { key: 'infrastructure', icon: 'IN', title: 'Infrastructure', status: 'Stable', statusTone: 'good',
      mainKpi: 'All core services online', summary: 'Network, identity, and storage layers operating within plan.',
      kpis: [{ label: 'Network uptime', value: '99.9%' }, { label: 'Identity SSO', value: 'Up' }, { label: 'Storage used', value: '64%' }, { label: 'Backup status', value: 'Current' }],
      details: ['Network uptime 99.9% rolling 30-day', 'Identity SSO healthy', 'Storage at 64% of allocated capacity', 'Nightly backups verified and current'],
      primaryActionLabel: 'Infrastructure View', backActionLabel: 'Backup Status',
      primaryActionHref: '/system-status', backActionHref: '/it', lastUpdated: '7:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Uptime trend', title: '30-day rolling uptime %', chip: 'Above target', trend: UPTIME_TREND },
    { kicker: 'Ticket volume trend', title: 'Open ticket count by month', chip: 'Steady', trend: TICKET_TREND },
  ],

  activityKicker: 'IT activity',
  activityTitle: 'Recent IT events',
  activities: [
    'Deploy d196ab66 promoted to production successfully.',
    '12 new devices imaged and joined to domain.',
    'Auto-remediation playbook ran on 4 non-compliant endpoints.',
    'Tier 2 escalation closed for ticket #4419.',
    'Backup verification job completed without errors overnight.',
  ],

  quickActions: [
    { title: 'Open Helpdesk', eyebrow: 'Quick action', description: 'Review and triage open support tickets.', actionLabel: 'Open Tickets', href: '/it', allowedRoles: ['it'] },
    { title: 'System Status', eyebrow: 'Quick action', description: 'Inspect API, DB, and core service health.', actionLabel: 'Open Status', href: '/system-status', allowedRoles: ['it'] },
    { title: 'Release Readiness', eyebrow: 'Quick action', description: 'Review deploy pipeline and rollout status.', actionLabel: 'View Releases', href: '/release-readiness', allowedRoles: ['it'] },
    { title: 'Security Console', eyebrow: 'Quick action', description: 'Open security console for cert and threat review.', actionLabel: 'Open Security', href: '/security', allowedRoles: ['it'] },
  ],

  statusTitle: 'IT workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'API', state: 'OK' },
    { label: 'Database', state: 'OK' },
    { label: 'Identity SSO', state: 'Up' },
    { label: 'Backups', state: 'Current' },
  ],
};

