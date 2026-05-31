import { BASE_NOTE } from './_baseData.js';

const ALUMNI_TREND = [
  { month: 'Aug', value: 1820 }, { month: 'Sep', value: 1840 }, { month: 'Oct', value: 1858 },
  { month: 'Nov', value: 1862 }, { month: 'Dec', value: 1870 }, { month: 'Jan', value: 1882 },
  { month: 'Feb', value: 1894 }, { month: 'Mar', value: 1912 },
];
const GIVING_TREND = [
  { month: 'Aug', value: 14 }, { month: 'Sep', value: 16 }, { month: 'Oct', value: 18 },
  { month: 'Nov', value: 22 }, { month: 'Dec', value: 28 }, { month: 'Jan', value: 18 },
  { month: 'Feb', value: 20 }, { month: 'Mar', value: 22 },
];

export default {
  key: 'alumniRelations',
  activePath: '/alumni-relations-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'AR', name: 'Alumni Relations', role: 'Advancement â€” Alumni Engagement & Giving Programs' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Alumni Relations!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/alumniRelations/summary/',
  liveDataKey: 'alumniRelations',

  metrics: [
    { label: 'Registered Alumni', value: '1,912', detail: 'Active in alumni database â€” up 90 this year.', accent: 'navy' },
    { label: 'Giving Rate', value: '22%', detail: 'YTD alumni giving â€” up from 18% last year.', accent: 'emerald' },
    { label: 'Events YTD', value: '4', detail: 'Reunions, networking events, homecoming.', accent: 'blue' },
    { label: 'Engagement Score', value: '71', detail: 'Out of 100 â€” top quartile for regional schools.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Promote Homecoming registration', detail: 'May 17 event â€” 186 registered, target 300.', state: 'This week', tone: 'warn' },
    { title: 'Spring giving campaign final push', detail: 'Close March 31 â€” 22% rate, target 25%.', state: 'This week', tone: 'warn' },
    { title: 'Update lost alumni contact records', detail: '88 alumni with no valid email â€” research project.', state: 'Next month', tone: 'nominal' },
  ],
  prioritiesTitle: 'Alumni Relations priorities',

  alerts: [
    { title: 'Homecoming registration at 62% of goal', detail: '186 of 300 registered â€” early bird deadline April 1.', tone: 'warn' },
    { title: 'Spring campaign closes March 31', detail: 'At 22% giving rate â€” 3% gap to target.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'database', icon: 'DB', title: 'Alumni Database', status: 'Active', statusTone: 'good',
      mainKpi: '1,912 alumni registered', summary: 'Growing database â€” 90 new records added this year.',
      kpis: [{ label: 'Registered', value: '1,912' }, { label: 'New This Year', value: '90' }, { label: 'Unreachable', value: '88' }, { label: 'Classes', value: '1984â€“2025' }],
      details: ['1,912 alumni in active database', '90 new or reconnected alumni added this year', '88 records with no valid contact info', 'Classes 1984 through 2025 represented'],
      primaryActionLabel: 'View Database', backActionLabel: 'Add Record',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/alumni-relations-dashboard', lastUpdated: '8:00 AM' },
    { key: 'giving', icon: 'GV', title: 'Alumni Giving', status: 'Watch', statusTone: 'warn',
      mainKpi: '22% giving rate â€” 3% gap to goal', summary: 'Spring campaign closes March 31 â€” final push needed.',
      kpis: [{ label: 'Giving Rate', value: '22%' }, { label: 'Goal', value: '25%' }, { label: 'Campaign Closes', value: 'Mar 31' }, { label: 'Amount YTD', value: '$84,200' }],
      details: ['22% alumni giving rate YTD', 'Goal: 25% by end of spring campaign', '$84,200 received from alumni this year', 'Major gift conversations: 4 in progress'],
      primaryActionLabel: 'Giving Report', backActionLabel: 'Campaign Dashboard',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:05 AM' },
    { key: 'events', icon: 'EV', title: 'Events', status: 'Upcoming', statusTone: 'warn',
      mainKpi: 'Homecoming May 17 â€” 186/300 registered', summary: 'Early bird deadline April 1 â€” push registration.',
      kpis: [{ label: 'Next Event', value: 'May 17' }, { label: 'Registered', value: '186' }, { label: 'Target', value: '300' }, { label: 'Deadline', value: 'Apr 1' }],
      details: ['Spring Homecoming: May 17 on campus', '186 of 300 alumni registered', 'Early bird pricing ends April 1', 'Sponsor packages still available'],
      primaryActionLabel: 'Event Management', backActionLabel: 'Send Invites',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:10 AM' },
    { key: 'engagement', icon: 'EN', title: 'Engagement', status: 'Top Quartile', statusTone: 'good',
      mainKpi: 'Score 71/100 â€” top quartile', summary: 'Alumni engagement at highest level in school history.',
      kpis: [{ label: 'Score', value: '71/100' }, { label: 'Email Opens', value: '34%' }, { label: 'Event Attendance', value: '22%' }, { label: 'YOY Change', value: '+8' }],
      details: ['Engagement score 71 â€” up 8 points YOY', 'Email open rate: 34% (industry avg 22%)', '22% event attendance rate', 'Social media following: +14% this year'],
      primaryActionLabel: 'Engagement Report', backActionLabel: 'Communications',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:15 AM' },
    { key: 'mentorship', icon: 'MT', title: 'Mentorship', status: 'Active', statusTone: 'good',
      mainKpi: '24 active alumni mentors', summary: 'Alumni mentoring current students across 6 career areas.',
      kpis: [{ label: 'Mentors', value: '24' }, { label: 'Mentees', value: '24' }, { label: 'Areas', value: '6' }, { label: 'New Pairs', value: '8' }],
      details: ['24 alumni actively mentoring current seniors', '6 career focus areas: STEM, business, ministry, medicine, law, arts', '8 new mentor-mentee pairs this semester', 'Monthly mentor check-in call scheduled April 10'],
      primaryActionLabel: 'Mentorship Program', backActionLabel: 'Match Students',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/alumni-relations-dashboard', lastUpdated: '8:20 AM' },
    { key: 'recognition', icon: 'RN', title: 'Alumni Recognition', status: 'Planning', statusTone: 'good',
      mainKpi: 'Distinguished Alumni Award â€” nominations open', summary: 'Annual recognition at Homecoming May 17.',
      kpis: [{ label: 'Nominations', value: '11' }, { label: 'Award Categories', value: '3' }, { label: 'Decision By', value: 'May 1' }, { label: 'Event', value: 'May 17' }],
      details: ['11 nominations received for Distinguished Alumni', '3 award categories: Career, Service, Faith', 'Selection committee meets May 1', 'Award presented at Homecoming May 17'],
      primaryActionLabel: 'Award Nominations', backActionLabel: 'Event Planning',
      primaryActionHref: '/alumni-relations-dashboard', backActionHref: '/alumni-relations-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Database growth', title: 'Registered Alumni', chip: '1,912 (+90 YTD)', trend: ALUMNI_TREND },
    { kicker: 'Alumni giving', title: 'Monthly Giving Rate (%)', chip: '22% YTD', trend: GIVING_TREND },
  ],

  activities: [
    'Homecoming registration push â€” 186/300 with early bird deadline April 1.',
    'Spring giving campaign at 22% â€” final push before March 31 close.',
    '11 Distinguished Alumni nominations received â€” committee convenes May 1.',
    '24 alumni mentors matched with current seniors.',
    '88 lost alumni records flagged for contact research.',
  ],

  quickActions: [
    { label: 'Alumni Database', href: '/alumni-relations-dashboard' },
    { label: 'Giving Report', href: '/alumni-relations-dashboard' },
    { label: 'Homecoming Event', href: '/alumni-relations-dashboard' },
    { label: 'Mentorship', href: '/alumni-relations-dashboard' },
  ],

  statuses: [
    { label: 'Registered Alumni', state: '1,912' },
    { label: 'Giving Rate', state: '22% (goal 25%)' },
    { label: 'Homecoming', state: '186/300 registered' },
    { label: 'Engagement Score', state: '71/100' },
  ],
};
