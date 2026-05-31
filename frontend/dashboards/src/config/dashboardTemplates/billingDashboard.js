import { BASE_NOTE } from './_baseData.js';

const BILLING_TREND = [
  { month: 'Aug', value: 92 }, { month: 'Sep', value: 156 }, { month: 'Oct', value: 210 },
  { month: 'Nov', value: 273 }, { month: 'Dec', value: 298 }, { month: 'Jan', value: 342 },
  { month: 'Feb', value: 381 }, { month: 'Mar', value: 412 },
];
const AR_TREND = [
  { month: 'Aug', value: 18 }, { month: 'Sep', value: 24 }, { month: 'Oct', value: 31 },
  { month: 'Nov', value: 29 }, { month: 'Dec', value: 22 }, { month: 'Jan', value: 28 },
  { month: 'Feb', value: 19 }, { month: 'Mar', value: 21 },
];

export default {
  key: 'billing',
  activePath: '/billing-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'BL', name: 'Billing Team', role: 'Finance â€” Billing & Collections' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Finance Team!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Billing widgets are currently populated from template snapshots pending live billing service integration.',
  note: 'Certification remains in review until billing dashboard metrics are served by canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/billing/summary/',
  liveDataKey: 'billing',
  metrics: [
    { label: 'Total Invoiced YTD', value: '$3.12M', detail: '94% of annual plan â€” ahead of schedule.', accent: 'emerald' },
    { label: 'Collection Rate', value: '96.4%', detail: '+1.2% vs last year â€” strong collection cadence.', accent: 'blue' },
    { label: 'Outstanding AR', value: '$21K', detail: '18 accounts â€” 12 under 30-day aging.', accent: 'gold' },
    { label: 'Overdue Accounts', value: '6', detail: '3 escalated â€” payment plans in progress.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Process April invoice batch', detail: '412 families â€” batch ready for send at 9 AM.', state: 'Today', tone: 'warn' },
    { title: 'Resolve 3 payment plan escalations', detail: 'Manual review required before month-end close.', state: 'This week', tone: 'warn' },
    { title: 'Confirm late fee waiver approvals', detail: '4 waiver requests pending admin sign-off.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Billing priorities',

  alerts: [
    { title: 'NSF check returned â€” family #2847', detail: 'Check reissue requested. Finance notified.', tone: 'warn' },
    { title: 'Payment portal maintenance window tonight', detail: 'Stripe scheduled 11 PMâ€“1 AM â€” no impact to invoicing.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'invoicing', icon: 'IN', title: 'Invoicing', status: 'On Track', statusTone: 'good',
      mainKpi: '$3.12M collected (94%)', summary: 'April batch ready â€” collection rate 96.4%.',
      kpis: [{ label: 'Invoiced YTD', value: '$3.12M' }, { label: 'Collected', value: '$3.01M' }, { label: 'Rate', value: '96.4%' }, { label: 'Batch Size', value: '412' }],
      details: ['April batch queued for 9 AM send', 'Auto-pay enrolled for 318 families', 'Manual pay: 94 families', 'Credit memos processed: 8'],
      primaryActionLabel: 'View Invoices', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:15 AM' },
    { key: 'ar', icon: 'AR', title: 'Accounts Receivable', status: 'Watch', statusTone: 'warn',
      mainKpi: '$21K outstanding (18 accounts)', summary: 'AR aging healthy â€” 3 escalations active.',
      kpis: [{ label: 'Outstanding', value: '$21K' }, { label: 'Accounts', value: '18' }, { label: '<30 days', value: '12' }, { label: 'Escalated', value: '3' }],
      details: ['6 overdue accounts flagged', '3 on approved payment plans', 'Collections follow-up sent to 6 families', 'NSF check pending reissue'],
      primaryActionLabel: 'View AR', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:20 AM' },
    { key: 'paymentPlans', icon: 'PP', title: 'Payment Plans', status: 'Stable', statusTone: 'good',
      mainKpi: '34 active plans', summary: 'All plans current â€” 3 require manual review.',
      kpis: [{ label: 'Active Plans', value: '34' }, { label: 'Current', value: '31' }, { label: 'Behind', value: '3' }, { label: 'Avg Balance', value: '$620' }],
      details: ['31 plans current through April', '3 plans past due â€” escalated to admin', 'New plan requests: 2 this week', 'Average plan duration: 10 months'],
      primaryActionLabel: 'Manage Plans', backActionLabel: 'View Reports',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:10 AM' },
    { key: 'aidAdjust', icon: 'FA', title: 'Aid Adjustments', status: 'Stable', statusTone: 'good',
      mainKpi: '87 aid accounts active', summary: 'Aid disbursements on schedule â€” no pending disputes.',
      kpis: [{ label: 'Aid Accounts', value: '87' }, { label: 'Disbursed YTD', value: '$210K' }, { label: 'Disputes', value: '0' }, { label: 'Pending', value: '4' }],
      details: ['4 new aid awards pending billing adjustment', 'All disbursements current through March', 'No disputes in queue', 'Spring aid renewals: 12 pending'],
      primaryActionLabel: 'Open Financial Aid', backActionLabel: 'View Disbursements',
      primaryActionHref: '/financial-aid-dashboard', backActionHref: '/finance', lastUpdated: '7:55 AM' },
    { key: 'waivers', icon: 'WV', title: 'Waivers & Credits', status: 'Watch', statusTone: 'warn',
      mainKpi: '4 waiver requests pending', summary: 'Late fee waivers need admin sign-off this week.',
      kpis: [{ label: 'Pending', value: '4' }, { label: 'Approved YTD', value: '12' }, { label: 'Denied', value: '2' }, { label: 'Credits Issued', value: '$1,240' }],
      details: ['4 late fee waivers awaiting approval', '12 waivers approved this year', 'Credit memos: $1,240 issued this month', 'Hardship review: 1 active case'],
      primaryActionLabel: 'Review Waivers', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:00 AM' },
    { key: 'reporting', icon: 'RP', title: 'Billing Reports', status: 'Stable', statusTone: 'good',
      mainKpi: 'April report ready', summary: 'Month-end billing report ready for finance review.',
      kpis: [{ label: 'Reports Ready', value: '4' }, { label: 'YTD Revenue', value: '$3.12M' }, { label: 'April Revenue', value: '$312K' }, { label: 'Audit Ready', value: 'Yes' }],
      details: ['April billing report generated', 'Year-to-date summary current', 'Audit trail export available', 'Board finance report due May 15'],
      primaryActionLabel: 'View Reports', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:30 AM' },
  ],

  trendPanels: [
    { kicker: 'Monthly invoicing', title: 'Revenue Collected YTD', chip: '+6% vs plan', trend: BILLING_TREND },
    { kicker: 'AR aging', title: 'Outstanding AR Balance', chip: '$21K current', trend: AR_TREND },
  ],

  activities: [
    'April invoice batch queued â€” 412 families notified.',
    'Payment plan #2841 brought current after family call.',
    'NSF check #2847 flagged â€” reissue requested.',
    'Late fee waiver submitted for admin review.',
    'Year-to-date billing summary exported for board.',
  ],

  quickActions: [
    { label: 'View Invoices', href: '/finance' },
    { label: 'Open Finance', href: '/finance' },
    { label: 'Financial Aid', href: '/financial-aid-dashboard' },
    { label: 'Reports', href: '/finance' },
  ],

  statuses: [
    { label: 'Billing System', state: 'Healthy' },
    { label: 'Payment Portal', state: 'Scheduled maint.' },
    { label: 'Aid Disbursements', state: 'On schedule' },
    { label: 'AR Aging', state: 'Stable' },
  ],
};

