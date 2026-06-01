import { LIVE_NOTE } from './_baseData.js';

const ENROLLMENT_TREND = [
  { month: 'Apr', value: 48 },
  { month: 'May', value: 61 },
  { month: 'Jun', value: 73 },
  { month: 'Jul', value: 79 },
];

export default {
  key: 'summerCamp',
  activePath: '/summer-camp-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: {
    initials: 'SC',
    name: 'Summer Camp Operations',
    role: 'Seasonal Program Director',
  },
  eyebrow: 'CROWN Launch Preview',
  title: 'Summer program command center',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/summerCamp/summary/',
  liveDataKey: 'summerCamp',

  metrics: [
    { label: 'Registered Campers', value: '79', detail: 'Capacity target is 84 students this cycle.', accent: 'blue' },
    { label: 'Staffed Sessions', value: '11', detail: 'All morning blocks staffed; two afternoon swaps pending.', accent: 'emerald' },
    { label: 'Waitlist Families', value: '9', detail: 'Priority callbacks due before noon.', accent: 'gold' },
    { label: 'Transport Confirmed', value: '92%', detail: 'Route confirmations in final review window.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Finalize counselor staffing swaps', detail: 'Two PM blocks still need confirmation today.', state: 'Today', tone: 'warn' },
    { title: 'Call top 9 waitlist families', detail: 'Offer open seats before orientation packet lock.', state: 'Today', tone: 'warn' },
    { title: 'Publish week-one route sheet', detail: 'Transportation lead requires approved roster export.', state: 'Ready', tone: 'good' },
  ],
  prioritiesTitle: 'Summer Camp priorities',

  alerts: [
    { title: 'Two afternoon sessions have unconfirmed counselors', detail: 'Resolve assignment before 2:00 PM staffing freeze.', tone: 'warn' },
    { title: 'Route sheet is waiting on final roster export', detail: 'Enrollment cutoff closes in 4 hours.', tone: 'warn' },
  ],

  trendPanels: [
    {
      kicker: 'Enrollment momentum',
      title: 'Camp registration trend',
      chip: '79 registered',
      trend: ENROLLMENT_TREND,
    },
  ],

  activities: [
    'Registration desk confirmed 7 new signups this week.',
    'Transportation coordinator requested final roster export.',
    'Counselor onboarding packets sent to all assigned staff.',
  ],

  quickActions: [
    { label: 'Open Camp Roster', href: '/summer-camp-dashboard' },
    { label: 'Staff Coverage', href: '/summer-camp-dashboard' },
    { label: 'Family Outreach', href: '/communications-dashboard' },
  ],

  statuses: [
    { label: 'Enrollment', state: '79 registered' },
    { label: 'Staffing', state: '2 confirmations pending' },
    { label: 'Transportation', state: '92% complete' },
    { label: 'Waitlist', state: '9 families' },
  ],
};
