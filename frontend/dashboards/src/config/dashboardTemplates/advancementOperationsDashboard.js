import { BASE_NOTE } from './_baseData.js';

const GRANT_TREND = [
  { month: 'Aug', value: 1 }, { month: 'Sep', value: 2 }, { month: 'Oct', value: 3 },
  { month: 'Nov', value: 4 }, { month: 'Dec', value: 4 }, { month: 'Jan', value: 5 },
  { month: 'Feb', value: 6 }, { month: 'Mar', value: 8 },
];
const DONOR_TREND = [
  { month: 'Aug', value: 88 }, { month: 'Sep', value: 102 }, { month: 'Oct', value: 118 },
  { month: 'Nov', value: 142 }, { month: 'Dec', value: 164 }, { month: 'Jan', value: 148 },
  { month: 'Feb', value: 156 }, { month: 'Mar', value: 168 },
];

export default {
  key: 'advancementOperations',
  activePath: '/advancement-operations-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'AO', name: 'Advancement Operations', role: 'Advancement — Fundraising Operations & Donor Relations' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Advancement Ops!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Active Grants', value: '8', detail: '8 grants in pipeline — $420K total ask.', accent: 'blue' },
    { label: 'Campaign Revenue', value: '$186K', detail: 'Spring campaign YTD — 74% of $250K goal.', accent: 'emerald' },
    { label: 'Donor Pipeline', value: '168', detail: 'Active donors in cultivation cycle this month.', accent: 'gold' },
    { label: 'Appeals Sent', value: '4', detail: '4 direct appeals this semester — 24% response rate.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Submit Lilly Foundation grant application', detail: '$80K ask — deadline April 30. Draft 90% complete.', state: 'This week', tone: 'warn' },
    { title: 'Close spring campaign — $64K gap to goal', detail: 'Campaign ends April 30 — final push to 168 active donors.', state: 'This week', tone: 'warn' },
    { title: 'Schedule major donor cultivation meetings', detail: '12 prospects in final cultivation stage — schedule April calls.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Advancement Ops priorities',

  alerts: [
    { title: 'Lilly Foundation grant deadline April 30', detail: '$80K ask — application draft at 90%, finalize this week.', tone: 'warn' },
    { title: 'Spring campaign $64K short of goal', detail: 'Campaign closes April 30 — donor engagement needed.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'grants', icon: 'GR', title: 'Grants', status: 'Active', statusTone: 'warn',
      mainKpi: '8 grants — $420K total ask', summary: 'Lilly Foundation deadline April 30 — prioritize.',
      kpis: [{ label: 'Active', value: '8' }, { label: 'Total Ask', value: '$420K' }, { label: 'Submitted', value: '3' }, { label: 'Pending', value: '5' }],
      details: ['8 grants in active pipeline', '$420K total requested funding', '3 grants submitted — awaiting decision', 'Lilly Foundation: $80K — due April 30'],
      primaryActionLabel: 'Grant Tracker', backActionLabel: 'Submit Grant',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-operations-dashboard', lastUpdated: '8:00 AM' },
    { key: 'campaign', icon: 'CP', title: 'Spring Campaign', status: 'Watch', statusTone: 'warn',
      mainKpi: '$186K of $250K — 74% to goal', summary: 'Campaign closes April 30 — $64K gap.',
      kpis: [{ label: 'Raised', value: '$186K' }, { label: 'Goal', value: '$250K' }, { label: 'Gap', value: '$64K' }, { label: 'Closes', value: 'April 30' }],
      details: ['$186,000 raised in spring campaign', 'Goal: $250,000 by April 30', '$64K gap with 2 weeks remaining', '24% donor response rate on appeals'],
      primaryActionLabel: 'Campaign Dashboard', backActionLabel: 'Donor List',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:05 AM' },
    { key: 'donors', icon: 'DN', title: 'Donor Pipeline', status: 'Active', statusTone: 'good',
      mainKpi: '168 active donors — 12 major gift prospects', summary: 'Strong pipeline — 12 prospects ready for major gift ask.',
      kpis: [{ label: 'Active Donors', value: '168' }, { label: 'Major Gift', value: '12' }, { label: 'New This Month', value: '24' }, { label: 'Avg Gift', value: '$1,107' }],
      details: ['168 donors in active cultivation', '12 prospects in major gift stage (>$10K)', '24 new donors added this month', 'Average gift: $1,107'],
      primaryActionLabel: 'Donor Pipeline', backActionLabel: 'Cultivation',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-operations-dashboard', lastUpdated: '8:10 AM' },
    { key: 'appeals', icon: 'AP', title: 'Appeals', status: 'Active', statusTone: 'good',
      mainKpi: '4 appeals — 24% response rate', summary: 'Response rate above sector average of 18%.',
      kpis: [{ label: 'Appeals Sent', value: '4' }, { label: 'Response Rate', value: '24%' }, { label: 'Responses', value: '312' }, { label: 'Revenue', value: '$48K' }],
      details: ['4 direct appeals sent this semester', '312 donors responded — 24% rate', '$48,000 raised from appeals alone', 'Next appeal: May 1 — year-end preview'],
      primaryActionLabel: 'Appeals Dashboard', backActionLabel: 'Create Appeal',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:15 AM' },
    { key: 'events', icon: 'EV', title: 'Fundraising Events', status: 'Upcoming', statusTone: 'good',
      mainKpi: 'Spring Gala — May 9', summary: 'Flagship fundraiser — $60K goal, 240 guests expected.',
      kpis: [{ label: 'Event', value: 'May 9' }, { label: 'Goal', value: '$60K' }, { label: 'Tickets Sold', value: '186' }, { label: 'Sponsorships', value: '$24K' }],
      details: ['Spring Gala: May 9, 6:00 PM', '$60,000 revenue goal', '186 of 240 tickets sold', '$24,000 in sponsorships secured'],
      primaryActionLabel: 'Gala Planning', backActionLabel: 'Ticket Sales',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-operations-dashboard', lastUpdated: '8:20 AM' },
    { key: 'reporting', icon: 'RP', title: 'Advancement Reporting', status: 'Current', statusTone: 'good',
      mainKpi: 'YTD report current', summary: 'Q1 advancement report ready for board.',
      kpis: [{ label: 'YTD Raised', value: '$186K' }, { label: 'Donors', value: '168' }, { label: 'Grants Active', value: '8' }, { label: 'Board Report', value: 'Ready' }],
      details: ['$186K raised YTD — campaign + grants + appeals', '168 active donors in pipeline', 'Q1 board advancement report ready', 'Next report: June board meeting'],
      primaryActionLabel: 'View Reports', backActionLabel: 'Export',
      primaryActionHref: '/advancement-operations-dashboard', backActionHref: '/advancement-operations-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Grant pipeline', title: 'Active Grants in Pipeline', chip: '8 active ($420K)', trend: GRANT_TREND },
    { kicker: 'Donor engagement', title: 'Active Donors in Cultivation', chip: '168 this month', trend: DONOR_TREND },
  ],

  activities: [
    'Lilly Foundation grant application 90% complete — final review needed.',
    'Spring campaign at $186K — $64K gap with 2 weeks remaining.',
    '12 major gift prospects ready for cultivation meetings.',
    '186 Spring Gala tickets sold — $24K in sponsorships secured.',
    '24 new donors added this month — pipeline strongest of year.',
  ],

  quickActions: [
    { label: 'Grant Tracker', href: '/advancement-operations-dashboard' },
    { label: 'Campaign Dashboard', href: '/advancement-dashboard' },
    { label: 'Donor Pipeline', href: '/advancement-operations-dashboard' },
    { label: 'Gala Planning', href: '/advancement-operations-dashboard' },
  ],

  statuses: [
    { label: 'Spring Campaign', state: '$186K (74% goal)' },
    { label: 'Grants', state: '8 active ($420K ask)' },
    { label: 'Active Donors', state: '168 in cultivation' },
    { label: 'Gala', state: '186/240 tickets sold' },
  ],
};
