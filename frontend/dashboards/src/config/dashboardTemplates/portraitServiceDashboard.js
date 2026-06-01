import { LIVE_NOTE } from './_baseData.js';

const HRS_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 240 }, { month: 'Oct', value: 480 },
  { month: 'Nov', value: 720 }, { month: 'Dec', value: 840 }, { month: 'Jan', value: 1080 },
  { month: 'Feb', value: 1320 }, { month: 'Mar', value: 1560 },
];
const PART_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 82 }, { month: 'Oct', value: 114 },
  { month: 'Nov', value: 128 }, { month: 'Dec', value: 118 }, { month: 'Jan', value: 134 },
  { month: 'Feb', value: 142 }, { month: 'Mar', value: 148 },
];

export default {
  key: 'portraitService',
  activePath: '/portrait-service-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'SH', name: 'Service Hours Coordinator', role: 'Student Life â€” Service Learning & Portrait Hours' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Service Learning!',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/portraitService/summary/',
  liveDataKey: 'portraitService',

  metrics: [
    { label: 'Service Hours Logged', value: '1,560', detail: 'YTD â€” averaging 10.5 hours per student.', accent: 'emerald' },
    { label: 'Students Participating', value: '148', detail: '24% of enrollment â€” 8thâ€“12th grade eligible.', accent: 'blue' },
    { label: 'Active Projects', value: '12', detail: '7 on-campus, 5 community partner projects.', accent: 'gold' },
    { label: 'Hours Due (Senior)', value: '82', detail: '14 seniors below 40-hour graduation requirement.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Contact 14 seniors below requirement', detail: '14 seniors need 40+ hours â€” deadline June 1.', state: 'This week', tone: 'warn' },
    { title: 'Approve 34 pending hour submissions', detail: '34 student submissions awaiting coordinator review.', state: 'Today', tone: 'warn' },
    { title: 'Confirm summer project placements', detail: '12 students registered for summer service projects.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Service Learning priorities',

  alerts: [
    { title: '14 seniors at risk of not meeting graduation requirement', detail: 'Service hours deadline June 1 â€” outreach needed immediately.', tone: 'warn' },
    { title: '34 hour submissions pending approval', detail: 'Students waiting for confirmation â€” review today.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'hours', icon: 'HR', title: 'Hours Tracking', status: 'On Track', statusTone: 'good',
      mainKpi: '1,560 hours logged YTD', summary: 'Strong participation â€” 34 submissions pending review.',
      kpis: [{ label: 'Hours YTD', value: '1,560' }, { label: 'Avg Per Student', value: '10.5' }, { label: 'Pending Review', value: '34' }, { label: 'Approved', value: '1,480' }],
      details: ['1,560 total service hours logged', 'Average 10.5 hours per participating student', '34 submissions awaiting coordinator review', '1,480 hours approved and credited'],
      primaryActionLabel: 'Review Submissions', backActionLabel: 'Hours Log',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/portrait-service-dashboard', lastUpdated: '8:00 AM' },
    { key: 'seniors', icon: 'SN', title: 'Senior Graduation Req.', status: 'Alert', statusTone: 'warn',
      mainKpi: '14 seniors below 40-hour minimum', summary: 'Graduation service requirement deadline June 1.',
      kpis: [{ label: 'At Risk', value: '14' }, { label: 'Minimum Hrs', value: '40' }, { label: 'Deadline', value: 'June 1' }, { label: 'Avg Hrs (Seniors)', value: '28' }],
      details: ['14 of 42 seniors below 40-hour requirement', 'Graduation service deadline: June 1', 'Average senior hours: 28', 'Urgent outreach needed for 14 students'],
      primaryActionLabel: 'Senior Report', backActionLabel: 'Contact Families',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:05 AM' },
    { key: 'projects', icon: 'PR', title: 'Service Projects', status: 'Active', statusTone: 'good',
      mainKpi: '12 active projects', summary: '7 on-campus, 5 community partner projects active.',
      kpis: [{ label: 'Projects', value: '12' }, { label: 'On-Campus', value: '7' }, { label: 'Community', value: '5' }, { label: 'Students', value: '148' }],
      details: ['7 on-campus projects: tutoring, beautification, library', '5 community partner projects active', 'New project proposals: 3 under review', 'All projects have faculty sponsor'],
      primaryActionLabel: 'View Projects', backActionLabel: 'Add Project',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/portrait-service-dashboard', lastUpdated: '8:10 AM' },
    { key: 'placements', icon: 'PL', title: 'Placements', status: 'Stable', statusTone: 'good',
      mainKpi: '148 students placed in projects', summary: 'Summer placements for 12 students being confirmed.',
      kpis: [{ label: 'Placed', value: '148' }, { label: 'Summer Reg.', value: '12' }, { label: 'Waitlist', value: '4' }, { label: 'Partner Sites', value: '8' }],
      details: ['148 students placed this academic year', '12 registered for summer service projects', '4 students on waitlist for popular projects', '8 community partner sites active'],
      primaryActionLabel: 'Manage Placements', backActionLabel: 'Partners',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/portrait-service-dashboard', lastUpdated: '8:15 AM' },
    { key: 'recognition', icon: 'RN', title: 'Recognition', status: 'Upcoming', statusTone: 'good',
      mainKpi: 'Service Learning Awards â€” May 30', summary: 'Top service learners recognized at end-of-year assembly.',
      kpis: [{ label: 'Top Performers', value: '10' }, { label: 'Award Categories', value: '4' }, { label: 'Event Date', value: 'May 30' }, { label: 'Nominations Due', value: 'May 15' }],
      details: ['Service Learning Awards ceremony May 30', '4 award categories: individual, group, faculty, project', 'Top 10 students by hours eligible', 'Nominations open to faculty now'],
      primaryActionLabel: 'Recognition Planning', backActionLabel: 'View Report',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/portrait-service-dashboard', lastUpdated: '8:20 AM' },
    { key: 'reporting', icon: 'RP', title: 'Reports', status: 'Stable', statusTone: 'good',
      mainKpi: 'YTD report current', summary: 'Service learning report ready for board and diocese.',
      kpis: [{ label: 'Hours YTD', value: '1,560' }, { label: 'Participants', value: '148' }, { label: 'Projects', value: '12' }, { label: 'Senior Req.', value: '75%' }],
      details: ['75% of seniors meeting requirement', 'Year-to-date summary current', 'Diocese service learning report due June 15', 'Board presentation scheduled May board meeting'],
      primaryActionLabel: 'View Reports', backActionLabel: 'Export Data',
      primaryActionHref: '/portrait-service-dashboard', backActionHref: '/portrait-service-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Service hour accumulation', title: 'Total Hours Logged YTD', chip: '1,560 hours', trend: HRS_TREND },
    { kicker: 'Student participation', title: 'Students Participating', chip: '148 this month', trend: PART_TREND },
  ],

  activities: [
    'Outreach sent to 14 seniors below graduation requirement.',
    '34 hour submissions queued for coordinator review.',
    '12 students confirmed for summer project placements.',
    'Service Learning Awards nominations opened to faculty.',
    '1,560 service hours logged â€” strong YTD progress.',
  ],

  quickActions: [
    { label: 'Review Submissions', href: '/portrait-service-dashboard' },
    { label: 'Senior Report', href: '/portrait-service-dashboard' },
    { label: 'View Projects', href: '/portrait-service-dashboard' },
    { label: 'Contact Families', href: '/communications-dashboard' },
  ],

  statuses: [
    { label: 'Hours YTD', state: '1,560 logged' },
    { label: 'Seniors at Risk', state: '14 below req.' },
    { label: 'Submissions', state: '34 pending review' },
    { label: 'Summer Placement', state: '12 registered' },
  ],
};
