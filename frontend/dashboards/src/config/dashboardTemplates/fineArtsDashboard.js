import { LIVE_NOTE } from './_baseData.js';

const PERF_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 1 }, { month: 'Oct', value: 2 },
  { month: 'Nov', value: 3 }, { month: 'Dec', value: 2 }, { month: 'Jan', value: 1 },
  { month: 'Feb', value: 2 }, { month: 'Mar', value: 3 },
];
const ENROLL_TREND = [
  { month: 'Aug', value: 82 }, { month: 'Sep', value: 88 }, { month: 'Oct', value: 91 },
  { month: 'Nov', value: 93 }, { month: 'Dec', value: 94 }, { month: 'Jan', value: 96 },
  { month: 'Feb', value: 98 }, { month: 'Mar', value: 104 },
];

export default {
  key: 'fineArts',
  activePath: '/fine-arts-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'FA', name: 'Fine Arts Department', role: 'Arts â€” Music, Visual Arts & Drama' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Fine Arts!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Fine arts widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until fine arts metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/fineArts/summary/',
  liveDataKey: 'fineArts',
  metrics: [
    { label: 'Enrolled Students', value: '104', detail: '17% of school â€” music 62, visual arts 28, drama 14.', accent: 'blue' },
    { label: 'Performances Upcoming', value: '3', detail: 'Spring Concert May 9, Drama May 16, Art Show May 23.', accent: 'gold' },
    { label: 'Rehearsals Today', value: '4', label2: 'Today', detail: 'Orchestra 7:30 AM, Choir 3 PM, Drama 3:30, Band 4 PM.', accent: 'emerald' },
    { label: 'Equipment Issues', value: '2', detail: 'Piano tuning due, 1 trumpet valve repair needed.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Spring Concert run-through rehearsal', detail: 'Orchestra + Choir combined rehearsal 7:30 AM today.', state: 'Today', tone: 'nominal' },
    { title: 'Order Drama props and costumes', detail: 'Purchase order needs principal approval by Thursday.', state: 'This week', tone: 'warn' },
    { title: 'Submit Spring Concert program to Print', detail: 'Program artwork and names due to office by April 29.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Fine Arts priorities',

  alerts: [
    { title: 'Drama props PO needs approval', detail: 'Purchase order submitted to principal â€” $840 budget.', tone: 'warn' },
    { title: 'Spring Concert program due to print April 29', detail: 'Program content finalized â€” send to office immediately.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'music', icon: 'MU', title: 'Music Programs', status: 'Active', statusTone: 'good',
      mainKpi: '62 students â€” Orchestra, Band, Choir', summary: 'Spring Concert May 9 â€” combined rehearsal today.',
      kpis: [{ label: 'Enrolled', value: '62' }, { label: 'Orchestra', value: '24' }, { label: 'Band', value: '19' }, { label: 'Choir', value: '19' }],
      details: ['Spring Concert: May 9, 7 PM', 'Combined rehearsal today 7:30 AM', 'Program due to print April 29', 'Soloists confirmed â€” 4 featured students'],
      primaryActionLabel: 'Music Programs', backActionLabel: 'Schedule',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:00 AM' },
    { key: 'drama', icon: 'DR', title: 'Drama', status: 'Active', statusTone: 'warn',
      mainKpi: '14 students â€” Spring Production May 16', summary: 'Props PO pending approval â€” costumes needed.',
      kpis: [{ label: 'Enrolled', value: '14' }, { label: 'Production', value: 'May 16' }, { label: 'Rehearsals', value: '3x/week' }, { label: 'PO Pending', value: '$840' }],
      details: ['Spring production: May 16, 6:30 PM', 'Rehearsals: Mon, Wed, Thu afternoons', 'Props/costumes PO pending principal approval', 'Set design: 80% complete'],
      primaryActionLabel: 'Drama Program', backActionLabel: 'Facilities',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:05 AM' },
    { key: 'visualArts', icon: 'VA', title: 'Visual Arts', status: 'Active', statusTone: 'good',
      mainKpi: '28 students â€” Art Show May 23', summary: 'Gallery setup begins May 20 â€” student works in progress.',
      kpis: [{ label: 'Enrolled', value: '28' }, { label: 'Art Show', value: 'May 23' }, { label: 'Works Submitted', value: '16' }, { label: 'Gallery Ready', value: 'May 20' }],
      details: ['Spring Art Show: May 23, 6 PM', '16 student works submitted so far', '12 works still in progress', 'Gallery setup: May 20â€“22'],
      primaryActionLabel: 'Visual Arts', backActionLabel: 'Art Show Planning',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/fine-arts-dashboard', lastUpdated: '8:10 AM' },
    { key: 'equipment', icon: 'EQ', title: 'Equipment', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 equipment issues', summary: 'Piano tuning overdue + trumpet valve repair needed.',
      kpis: [{ label: 'Issues', value: '2' }, { label: 'Piano Tuning', value: 'Overdue' }, { label: 'Trumpet Repair', value: 'Ordered' }, { label: 'Inventory', value: 'Current' }],
      details: ['Grand piano: tuning overdue by 2 months', 'Trumpet valve repair ordered from music shop', 'Full inventory count completed April 15', 'Annual equipment inspection scheduled May 1'],
      primaryActionLabel: 'Equipment Log', backActionLabel: 'Facilities',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:15 AM' },
    { key: 'performances', icon: 'PF', title: 'Performances', status: 'Upcoming', statusTone: 'good',
      mainKpi: '3 performances in May', summary: 'Concert May 9, Drama May 16, Art Show May 23.',
      kpis: [{ label: 'This Month', value: '0' }, { label: 'May', value: '3' }, { label: 'Total YTD', value: '6' }, { label: 'Tickets Open', value: 'Yes' }],
      details: ['Spring Concert: May 9, 7 PM â€” tickets open', 'Drama production: May 16, 6:30 PM', 'Spring Art Show: May 23, 6 PM', 'Year-end performance total: 6 events'],
      primaryActionLabel: 'View Schedule', backActionLabel: 'Ticket Sales',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/fine-arts-dashboard', lastUpdated: '8:20 AM' },
    { key: 'community', icon: 'CM', title: 'Community & Outreach', status: 'Stable', statusTone: 'good',
      mainKpi: '3 community partnerships active', summary: 'Philharmonic visit, art contest, church concert links.',
      kpis: [{ label: 'Partnerships', value: '3' }, { label: 'Community Concerts', value: '1' }, { label: 'Contest Entries', value: '4' }, { label: 'Scholarship Apps', value: '2' }],
      details: ['City Philharmonic school visit: May 7', 'Regional art contest: 4 student entries', 'Church holiday concert partnership active', '2 students applying for arts scholarships'],
      primaryActionLabel: 'Community Programs', backActionLabel: 'View Reports',
      primaryActionHref: '/fine-arts-dashboard', backActionHref: '/fine-arts-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Performance events', title: 'Performances Per Month', chip: '3 events in May', trend: PERF_TREND },
    { kicker: 'Arts enrollment', title: 'Students in Fine Arts', chip: '104 enrolled (17%)', trend: ENROLL_TREND },
  ],

  activities: [
    'Spring Concert combined rehearsal at 7:30 AM â€” Orchestra + Choir.',
    'Drama props purchase order submitted for principal approval.',
    'Spring Concert program sent to admin office for printing.',
    'Trumpet valve repair order placed with music shop.',
    '16 student art works submitted for Spring Art Show.',
  ],

  quickActions: [
    { label: 'Music Programs', href: '/fine-arts-dashboard' },
    { label: 'Drama', href: '/fine-arts-dashboard' },
    { label: 'Performance Calendar', href: '/fine-arts-dashboard' },
    { label: 'Equipment Log', href: '/fine-arts-dashboard' },
  ],

  statuses: [
    { label: 'Enrollment', state: '104 students' },
    { label: 'Props PO', state: 'Pending approval' },
    { label: 'Next Performance', state: 'May 9' },
    { label: 'Equipment', state: '2 issues' },
  ],
};

