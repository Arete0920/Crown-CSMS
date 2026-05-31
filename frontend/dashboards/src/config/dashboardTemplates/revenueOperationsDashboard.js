import { BASE_NOTE } from './_baseData.js';

const REV_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 142000 }, { month: 'Oct', value: 288000 },
  { month: 'Nov', value: 446000 }, { month: 'Dec', value: 612000 }, { month: 'Jan', value: 786000 },
  { month: 'Feb', value: 968000 }, { month: 'Mar', value: 1144000 },
];
const COL_TREND = [
  { month: 'Aug', value: 94 }, { month: 'Sep', value: 95 }, { month: 'Oct', value: 96 },
  { month: 'Nov', value: 96 }, { month: 'Dec', value: 97 }, { month: 'Jan', value: 97 },
  { month: 'Feb', value: 98 }, { month: 'Mar', value: 98 },
];

export default {
  key: 'revenueOperations',
  activePath: '/revenue-operations-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'RO', name: 'Revenue Operations', role: 'Platform â€” Revenue & Subscription Management' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Revenue Ops!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/revenueOperations/summary/',
  liveDataKey: 'revenueOperations',

  metrics: [
    { label: 'Revenue YTD', value: '$1.14M', detail: 'Subscription and service revenue â€” on plan.', accent: 'emerald' },
    { label: 'ARR Pipeline', value: '$280K', detail: '8 open deals â€” Q2 close opportunity.', accent: 'blue' },
    { label: 'Collection Rate', value: '98%', detail: 'March billing â€” $18,400 outstanding.', accent: 'gold' },
    { label: 'Churn Risk', value: '2', detail: '2 accounts flagged â€” renewal in 60 days.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Renew 2 at-risk accounts before May 30', detail: 'Covenant and Jefferson flagged â€” engage within 2 weeks.', state: 'This week', tone: 'warn' },
    { title: 'Close Q2 pipeline deals', detail: '$280K ARR in 8 open deals â€” 3 ready to close.', state: 'This month', tone: 'nominal' },
    { title: 'Collect $18,400 outstanding March billing', detail: '3 accounts overdue â€” reminders sent, escalation needed.', state: 'Today', tone: 'warn' },
  ],
  prioritiesTitle: 'Revenue Operations priorities',

  alerts: [
    { title: '2 accounts at churn risk â€” renewal 60 days', detail: 'Covenant and Jefferson â€” schedule renewal calls this week.', tone: 'warn' },
    { title: '$18,400 outstanding in March billing', detail: '3 overdue accounts â€” escalation needed beyond reminders.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'revenue', icon: 'RV', title: 'Revenue', status: 'On Plan', statusTone: 'good',
      mainKpi: '$1.14M YTD â€” on plan', summary: 'Revenue tracking to annual plan â€” slight Q1 outperformance.',
      kpis: [{ label: 'YTD', value: '$1.14M' }, { label: 'Annual Plan', value: '$1.8M' }, { label: 'Q1 Variance', value: '+$8K' }, { label: 'Monthly Run Rate', value: '$176K' }],
      details: ['$1.14M subscription and service revenue YTD', 'Annual plan: $1.8M â€” on pace', 'Q1 finished $8K ahead of plan', 'Monthly run rate: $176K'],
      primaryActionLabel: 'Revenue Report', backActionLabel: 'Finance',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/finance', lastUpdated: '8:00 AM' },
    { key: 'pipeline', icon: 'PP', title: 'ARR Pipeline', status: 'Active', statusTone: 'good',
      mainKpi: '$280K â€” 8 open deals', summary: '3 deals ready to close in Q2.',
      kpis: [{ label: 'Pipeline', value: '$280K' }, { label: 'Open Deals', value: '8' }, { label: 'Close-Ready', value: '3' }, { label: 'Avg Deal Size', value: '$35K' }],
      details: ['$280K total ARR pipeline', '8 open deals in various stages', '3 deals in final negotiation', 'Average deal size: $35K ARR'],
      primaryActionLabel: 'Pipeline View', backActionLabel: 'Deal Details',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/revenue-operations-dashboard', lastUpdated: '8:05 AM' },
    { key: 'collection', icon: 'CL', title: 'Collections', status: 'Watch', statusTone: 'warn',
      mainKpi: '98% collection rate â€” $18,400 outstanding', summary: '3 accounts overdue â€” escalation needed.',
      kpis: [{ label: 'Rate', value: '98%' }, { label: 'Outstanding', value: '$18,400' }, { label: 'Overdue Accts', value: '3' }, { label: 'Days Overdue', value: '14â€“28' }],
      details: ['98% collection rate for March billing', '$18,400 outstanding across 3 accounts', 'Account A: $8,200 â€” 28 days overdue', 'Account B: $6,400 â€” 21 days', 'Account C: $3,800 â€” 14 days'],
      primaryActionLabel: 'Collections Queue', backActionLabel: 'Billing',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/billing-dashboard', lastUpdated: '8:10 AM' },
    { key: 'churn', icon: 'CH', title: 'Churn Risk', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 accounts at risk â€” 60-day renewal', summary: 'Engage Covenant and Jefferson before end of week.',
      kpis: [{ label: 'At Risk', value: '2' }, { label: 'Renewal Window', value: '60 days' }, { label: 'Combined ARR', value: '$84K' }, { label: 'Risk Score', value: 'High' }],
      details: ['Covenant: renewal May 30 â€” satisfaction concern', 'Jefferson: renewal June 1 â€” implementation delays', 'Combined at-risk ARR: $84,000', 'Success team engagement needed this week'],
      primaryActionLabel: 'Churn Risk Report', backActionLabel: 'Renewal Plans',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:15 AM' },
    { key: 'expansion', icon: 'EX', title: 'Expansion Revenue', status: 'Active', statusTone: 'good',
      mainKpi: '$42K expansion ARR YTD', summary: 'Upsells and seat expansions tracking well.',
      kpis: [{ label: 'Expansion ARR', value: '$42K' }, { label: 'Accounts Expanded', value: '6' }, { label: 'Avg Expansion', value: '$7K' }, { label: 'Target', value: '$60K' }],
      details: ['$42K in expansion revenue YTD', '6 accounts expanded with add-ons or seats', 'Average expansion: $7,000 ARR', 'Target $60K expansion by year-end'],
      primaryActionLabel: 'Expansion Tracker', backActionLabel: 'Upsell Opps',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/revenue-operations-dashboard', lastUpdated: '8:20 AM' },
    { key: 'reporting', icon: 'RP', title: 'Revenue Reporting', status: 'Current', statusTone: 'good',
      mainKpi: 'Monthly revenue report published', summary: 'March report ready â€” Q2 forecast due April 15.',
      kpis: [{ label: 'March Report', value: 'Published' }, { label: 'Q2 Forecast', value: 'Due Apr 15' }, { label: 'Board Ready', value: 'Yes' }, { label: 'Accuracy', value: 'Â±2%' }],
      details: ['March revenue report published', 'Q2 forecast due April 15', 'Board presentation prepared', 'Forecast accuracy within Â±2% last 4 quarters'],
      primaryActionLabel: 'Revenue Reports', backActionLabel: 'Forecasting',
      primaryActionHref: '/revenue-operations-dashboard', backActionHref: '/revenue-operations-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Revenue accumulation', title: 'Revenue YTD ($)', chip: '$1.14M on plan', trend: REV_TREND },
    { kicker: 'Billing health', title: 'Collection Rate (%)', chip: '98% March', trend: COL_TREND },
  ],

  activities: [
    '2 churn-risk accounts identified â€” Covenant and Jefferson renewal calls needed.',
    '$18,400 outstanding in March billing â€” 3 accounts escalated.',
    '3 pipeline deals ready to close in Q2.',
    'March revenue report published â€” Q2 forecast due April 15.',
    '$42K expansion ARR YTD â€” 6 accounts expanded.',
  ],

  quickActions: [
    { label: 'Revenue Report', href: '/revenue-operations-dashboard' },
    { label: 'Pipeline', href: '/revenue-operations-dashboard' },
    { label: 'Collections', href: '/billing-dashboard' },
    { label: 'Churn Risk', href: '/revenue-operations-dashboard' },
  ],

  statuses: [
    { label: 'Revenue YTD', state: '$1.14M (on plan)' },
    { label: 'Churn Risk', state: '2 accounts (high)' },
    { label: 'Outstanding', state: '$18,400 (3 accts)' },
    { label: 'Pipeline', state: '$280K ARR' },
  ],
};
