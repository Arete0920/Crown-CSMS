import { BASE_NOTE } from './_baseData.js';

const DONOR_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 28 }, { month: 'Oct', value: 44 },
  { month: 'Nov', value: 68 }, { month: 'Dec', value: 112 }, { month: 'Jan', value: 124 },
  { month: 'Feb', value: 138 }, { month: 'Mar', value: 152 },
];
const FUND_TREND = [
  { month: 'Aug', value: 18 }, { month: 'Sep', value: 42 }, { month: 'Oct', value: 78 },
  { month: 'Nov', value: 124 }, { month: 'Dec', value: 186 }, { month: 'Jan', value: 204 },
  { month: 'Feb', value: 231 }, { month: 'Mar', value: 268 },
];

export default {
  key: 'advancement',
  activePath: '/advancement-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'AV', name: 'Advancement Office', role: 'Development — Fundraising & Donor Relations' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Advancement!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Donors YTD', value: '152', detail: '82% of annual donor goal — strong spring giving.', accent: 'emerald' },
    { label: 'Funds Raised', value: '$268K', detail: '74% of $362K annual campaign goal.', accent: 'blue' },
    { label: 'Active Campaigns', value: '3', detail: 'Annual Fund, Legacy Society, Spring Gala.', accent: 'gold' },
    { label: 'Donor Retention', value: '78%', detail: '+4% vs prior year — best retention since 2021.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Spring Gala follow-up pledges', detail: '18 pledge cards returned — need entry and thank-you letters.', state: 'Today', tone: 'warn' },
    { title: 'Major donor stewardship calls', detail: '6 donors at $5K+ level due for personal outreach.', state: 'This week', tone: 'warn' },
    { title: 'Annual Fund Q4 push strategy', detail: 'Planning meeting Thursday — 26% of goal remains.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Advancement priorities',

  alerts: [
    { title: '18 Spring Gala pledges need entry', detail: 'Pledge cards received — data entry and acknowledgment due.', tone: 'warn' },
    { title: 'Annual Fund at 74% — Q4 push needed', detail: '$94K remaining to goal — 6 weeks to fiscal year end.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'annualFund', icon: 'AF', title: 'Annual Fund', status: 'On Track', statusTone: 'good',
      mainKpi: '$268K raised (74% of $362K goal)', summary: 'Spring giving strong — Q4 push needed for final 26%.',
      kpis: [{ label: 'Raised', value: '$268K' }, { label: 'Goal', value: '$362K' }, { label: 'Progress', value: '74%' }, { label: 'Remaining', value: '$94K' }],
      details: ['Spring Gala raised $42K in one evening', 'Online giving up 18% vs last year', '152 unique donors this fiscal year', 'Major gift prospects: 6 in cultivation'],
      primaryActionLabel: 'View Annual Fund', backActionLabel: 'Donor Database',
      primaryActionHref: '/advancement-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:00 AM' },
    { key: 'donors', icon: 'DN', title: 'Donor Management', status: 'Active', statusTone: 'good',
      mainKpi: '152 donors — 78% retention rate', summary: 'Best retention since 2021 — major gift pipeline healthy.',
      kpis: [{ label: 'Donors', value: '152' }, { label: 'New', value: '26' }, { label: 'Retained', value: '119' }, { label: 'Lapsed', value: '7' }],
      details: ['152 unique donors this fiscal year', '26 new donors acquired', '119 donors retained from last year (78%)', '7 lapsed donors — reactivation outreach planned'],
      primaryActionLabel: 'Donor Database', backActionLabel: 'View History',
      primaryActionHref: '/advancement-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:05 AM' },
    { key: 'campaigns', icon: 'CP', title: 'Campaigns', status: 'Active', statusTone: 'good',
      mainKpi: '3 active campaigns', summary: 'Annual Fund, Legacy Society, Spring Gala all active.',
      kpis: [{ label: 'Active', value: '3' }, { label: 'Annual Fund', value: '74%' }, { label: 'Legacy Society', value: '6 members' }, { label: 'Gala Revenue', value: '$42K' }],
      details: ['Annual Fund: $268K raised of $362K', 'Legacy Society: 6 members, $1.2M in planned gifts', 'Spring Gala: $42K net — 18 pledges pending entry', 'Next campaign: Alumni Giving Day (May 14)'],
      primaryActionLabel: 'View Campaigns', backActionLabel: 'View Reports',
      primaryActionHref: '/advancement-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:10 AM' },
    { key: 'stewardship', icon: 'ST', title: 'Stewardship', status: 'Due', statusTone: 'warn',
      mainKpi: '6 major donor calls due this week', summary: 'Personal outreach needed for $5K+ donors.',
      kpis: [{ label: 'Calls Due', value: '6' }, { label: 'Thank-you Letters', value: '18' }, { label: 'Stewardship Reports', value: '3' }, { label: 'Events This Month', value: '1' }],
      details: ['6 major donors ($5K+) due for personal call', '18 pledge acknowledgment letters pending', '3 donor impact reports due Q2', 'Legacy Society dinner: May 20'],
      primaryActionLabel: 'View Stewardship', backActionLabel: 'Donor List',
      primaryActionHref: '/advancement-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:15 AM' },
    { key: 'events', icon: 'EV', title: 'Events', status: 'Upcoming', statusTone: 'good',
      mainKpi: 'Alumni Giving Day — May 14', summary: 'Next major event 3 weeks out — planning underway.',
      kpis: [{ label: 'Next Event', value: 'May 14' }, { label: 'Goal', value: '$25K' }, { label: 'Registrations', value: '0 (open)' }, { label: 'Past Events', value: '3' }],
      details: ['Spring Gala complete — $42K raised', 'Alumni Giving Day: May 14', 'Legacy Dinner: May 20', 'Annual Golf Tournament: June 12'],
      primaryActionLabel: 'Plan Events', backActionLabel: 'View Calendar',
      primaryActionHref: '/advancement-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:20 AM' },
    { key: 'grants', icon: 'GR', title: 'Grants & Foundations', status: 'Active', statusTone: 'good',
      mainKpi: '4 active grant applications', summary: 'Two grants awarded — two applications in review.',
      kpis: [{ label: 'Active Apps', value: '4' }, { label: 'Awarded YTD', value: '2' }, { label: 'Pending', value: '2' }, { label: 'Total Value', value: '$68K' }],
      details: ['2 grants awarded: $38K total', '2 applications in foundation review', 'Kern Family Foundation: pending ($20K)', 'Gates Education Grant: pending ($10K)'],
      primaryActionLabel: 'View Grants', backActionLabel: 'Open Reports',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-operations-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Donor acquisition', title: 'Unique Donors YTD', chip: '152 donors (+12%)', trend: DONOR_TREND },
    { kicker: 'Fundraising progress', title: 'Funds Raised ($K YTD)', chip: '$268K of $362K goal', trend: FUND_TREND },
  ],

  activities: [
    '18 Spring Gala pledge cards received — data entry pending.',
    '6 major donor stewardship calls scheduled for the week.',
    'Alumni Giving Day event page published (May 14).',
    'Kern Foundation grant application follow-up sent.',
    'Annual Fund Q4 strategy meeting scheduled Thursday.',
  ],

  quickActions: [
    { label: 'Donor Database', href: '/advancement-dashboard' },
    { label: 'View Campaigns', href: '/advancement-dashboard' },
    { label: 'Grant Applications', href: '/advancement-operations-dashboard' },
    { label: 'Event Planning', href: '/advancement-dashboard' },
  ],

  statuses: [
    { label: 'Annual Fund', state: '74% of goal' },
    { label: 'Donor Pipeline', state: 'Active' },
    { label: 'Stewardship', state: '6 calls due' },
    { label: 'Next Event', state: 'May 14' },
  ],
};
