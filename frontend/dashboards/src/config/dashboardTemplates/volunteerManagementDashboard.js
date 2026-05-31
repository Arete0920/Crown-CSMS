import { BASE_NOTE } from './_baseData.js';

const VOL_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 24 }, { month: 'Oct', value: 31 },
  { month: 'Nov', value: 38 }, { month: 'Dec', value: 22 }, { month: 'Jan', value: 28 },
  { month: 'Feb', value: 34 }, { month: 'Mar', value: 41 },
];
const HRS_TREND = [
  { month: 'Aug', value: 44 }, { month: 'Sep', value: 98 }, { month: 'Oct', value: 124 },
  { month: 'Nov', value: 148 }, { month: 'Dec', value: 86 }, { month: 'Jan', value: 112 },
  { month: 'Feb', value: 138 }, { month: 'Mar', value: 168 },
];

export default {
  key: 'volunteerManagement',
  activePath: '/volunteer-management-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'VM', name: 'Volunteer Coordinator', role: 'Community â€” Volunteer Programs & Family Engagement' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Volunteer Coordinator!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/volunteerManagement/summary/',
  liveDataKey: 'volunteerManagement',

  metrics: [
    { label: 'Volunteers Active', value: '41', detail: 'This month â€” up 21% from February.', accent: 'emerald' },
    { label: 'Hours This Month', value: '168', detail: 'March record â€” across 14 active programs.', accent: 'blue' },
    { label: 'Events Staffed', value: '6', detail: '6 volunteer-staffed events this month â€” all covered.', accent: 'gold' },
    { label: 'New Applications', value: '8', detail: '8 new volunteer applicants â€” background checks pending.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Process 8 new volunteer applications', detail: 'Background checks requested â€” clearance needed before placement.', state: 'This week', tone: 'warn' },
    { title: 'Staff Spring Gala volunteer team', detail: 'Need 24 volunteers for May 9 Gala â€” 18 confirmed so far.', state: 'This week', tone: 'warn' },
    { title: 'Send volunteer appreciation certificates', detail: 'Year-end recognition for all 41 active volunteers.', state: 'Next week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Volunteer priorities',

  alerts: [
    { title: '8 applications pending background clearance', detail: 'Cannot be placed until clearance received.', tone: 'warn' },
    { title: 'Spring Gala needs 6 more volunteers', detail: '24 needed â€” 18 confirmed for May 9 event.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'activeVols', icon: 'AV', title: 'Active Volunteers', status: 'Active', statusTone: 'good',
      mainKpi: '41 active volunteers this month', summary: 'Strongest volunteer engagement this year.',
      kpis: [{ label: 'Active', value: '41' }, { label: 'New Apps', value: '8' }, { label: 'YTD Total', value: '184' }, { label: 'Retention', value: '82%' }],
      details: ['41 volunteers active in March', '8 new applications pending clearance', '82% volunteer retention year-over-year', 'Average tenure: 2.4 years'],
      primaryActionLabel: 'Volunteer Roster', backActionLabel: 'Applications',
      primaryActionHref: '/volunteer-management-dashboard', backActionHref: '/volunteer-management-dashboard', lastUpdated: '8:00 AM' },
    { key: 'hours', icon: 'HR', title: 'Volunteer Hours', status: 'Record', statusTone: 'good',
      mainKpi: '168 hours in March â€” monthly record', summary: 'Highest single-month volunteer hours since launch.',
      kpis: [{ label: 'March Hours', value: '168' }, { label: 'YTD', value: '918' }, { label: 'Avg Per Vol', value: '4.1' }, { label: 'Programs Served', value: '14' }],
      details: ['168 hours logged in March â€” monthly record', '918 hours YTD across all programs', 'Average 4.1 hours per active volunteer', '14 distinct programs supported'],
      primaryActionLabel: 'Hours Log', backActionLabel: 'Reports',
      primaryActionHref: '/volunteer-management-dashboard', backActionHref: '/volunteer-management-dashboard', lastUpdated: '8:05 AM' },
    { key: 'applications', icon: 'AP', title: 'Applications', status: 'Pending', statusTone: 'warn',
      mainKpi: '8 applications â€” background checks pending', summary: 'New applicants cannot be placed until cleared.',
      kpis: [{ label: 'Pending', value: '8' }, { label: 'In Background Check', value: '8' }, { label: 'Approved YTD', value: '24' }, { label: 'Denied', value: '1' }],
      details: ['8 new applications submitted', 'All 8 in background check process', 'Average clearance time: 5 business days', '24 volunteers approved this year'],
      primaryActionLabel: 'Review Applications', backActionLabel: 'Clearance Status',
      primaryActionHref: '/volunteer-management-dashboard', backActionHref: '/volunteer-management-dashboard', lastUpdated: '8:10 AM' },
    { key: 'events', icon: 'EV', title: 'Event Staffing', status: 'Watch', statusTone: 'warn',
      mainKpi: 'Spring Gala: 6 volunteers short', summary: '24 needed for May 9 â€” 18 confirmed so far.',
      kpis: [{ label: 'Next Event', value: 'May 9' }, { label: 'Needed', value: '24' }, { label: 'Confirmed', value: '18' }, { label: 'Gap', value: '6' }],
      details: ['Spring Gala: May 9 â€” 6 PM', '24 volunteer positions identified', '18 confirmed â€” 6 still needed', 'Open positions: check-in, setup, cleanup'],
      primaryActionLabel: 'Recruit Volunteers', backActionLabel: 'Event Calendar',
      primaryActionHref: '/volunteer-management-dashboard', backActionHref: '/advancement-dashboard', lastUpdated: '8:15 AM' },
    { key: 'recognition', icon: 'RN', title: 'Recognition', status: 'Upcoming', statusTone: 'good',
      mainKpi: 'Year-end appreciation prep', summary: 'Certificates and recognition event being planned.',
      kpis: [{ label: 'Volunteers to Recognize', value: '41' }, { label: 'Certificates', value: '41' }, { label: 'Event Date', value: 'May 30' }, { label: 'Thank-you Notes', value: '41' }],
      details: ['41 certificates to print and sign', 'Year-end volunteer appreciation: May 30', 'Thank-you notes to send this week', 'Annual Volunteer of the Year award â€” nominations open'],
      primaryActionLabel: 'Recognition Planning', backActionLabel: 'Communications',
      primaryActionHref: '/communications-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:20 AM' },
    { key: 'programs', icon: 'PR', title: 'Volunteer Programs', status: 'Active', statusTone: 'good',
      mainKpi: '14 programs with volunteer support', summary: 'Volunteers active across all major program areas.',
      kpis: [{ label: 'Programs', value: '14' }, { label: 'Classroom Support', value: '6' }, { label: 'Events', value: '4' }, { label: 'Clubs/Activities', value: '4' }],
      details: ['6 programs: classroom reading support', '4 programs: event and fundraising support', '4 programs: clubs, athletics, library', 'All 14 programs have lead coordinator'],
      primaryActionLabel: 'View Programs', backActionLabel: 'Assignments',
      primaryActionHref: '/volunteer-management-dashboard', backActionHref: '/volunteer-management-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Volunteer engagement', title: 'Active Volunteers Per Month', chip: '41 in March (+21%)', trend: VOL_TREND },
    { kicker: 'Volunteer hours', title: 'Hours Logged Per Month', chip: '168 hrs (March record)', trend: HRS_TREND },
  ],

  activities: [
    '8 new volunteer applications sent for background clearance.',
    'Spring Gala recruitment: 6 positions still open for May 9.',
    'Year-end appreciation certificates drafted for 41 volunteers.',
    'March hours record confirmed: 168 hours logged.',
    'Reading support program matched 3 new volunteers to classrooms.',
  ],

  quickActions: [
    { label: 'Volunteer Roster', href: '/volunteer-management-dashboard' },
    { label: 'Applications', href: '/volunteer-management-dashboard' },
    { label: 'Event Staffing', href: '/advancement-dashboard' },
    { label: 'Hours Log', href: '/volunteer-management-dashboard' },
  ],

  statuses: [
    { label: 'Active Volunteers', state: '41 this month' },
    { label: 'Applications', state: '8 pending clearance' },
    { label: 'Gala Staffing', state: '18/24 confirmed' },
    { label: 'Hours YTD', state: '918 hours' },
  ],
};
