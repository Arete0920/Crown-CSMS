const PART_TREND = [
  { month: 'Aug', value: 180 }, { month: 'Sep', value: 214 }, { month: 'Oct', value: 228 },
  { month: 'Nov', value: 219 }, { month: 'Dec', value: 231 }, { month: 'Jan', value: 244 },
  { month: 'Feb', value: 256 }, { month: 'Mar', value: 268 },
];
const EVENT_TREND = [
  { month: 'Aug', value: 4 }, { month: 'Sep', value: 9 }, { month: 'Oct', value: 12 },
  { month: 'Nov', value: 11 }, { month: 'Dec', value: 7 }, { month: 'Jan', value: 10 },
  { month: 'Feb', value: 13 }, { month: 'Mar', value: 14 },
];

export default {
  key: 'activitiesAthletics',
  activePath: '/activities-athletics-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'AA', name: 'Activities & Athletics', role: 'Student Life â€” Activities & Athletic Programs' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Activities Team!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Activities and athletics widgets currently use template snapshots pending live program service integration.',
  note: 'Certification remains in review until activities and athletics metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/activitiesAthletics/summary/',
  liveDataKey: 'activitiesAthletics',
  metrics: [
    { label: 'Active Programs', value: '22', detail: '14 athletic, 8 activity clubs â€” all active.', accent: 'blue' },
    { label: 'Student Participation', value: '268', detail: '44% of enrollment â€” up 5% from last year.', accent: 'emerald' },
    { label: 'Events This Week', value: '7', detail: '3 home, 4 away â€” transportation confirmed.', accent: 'gold' },
    { label: 'Clearances Pending', value: '12', detail: '9 physicals, 3 permission slips outstanding.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Resolve 12 outstanding clearances', detail: '9 physicals, 3 permission slips â€” students cannot compete.', state: 'Today', tone: 'warn' },
    { title: 'Confirm bus for Friday away game', detail: 'Transportation pending confirmation for 2 teams.', state: 'Today', tone: 'warn' },
    { title: 'Submit spring season schedule to CSAA', detail: 'League submission deadline April 29.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Activities priorities',

  alerts: [
    { title: '9 student physicals expired or missing', detail: 'Students cannot participate until cleared â€” families notified.', tone: 'warn' },
    { title: 'CSAA spring schedule submission due April 29', detail: 'Draft complete â€” pending AD signature.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'programs', icon: 'PR', title: 'Programs', status: 'Active', statusTone: 'good',
      mainKpi: '22 active programs (268 students)', summary: '14 sports, 8 clubs â€” 44% participation rate.',
      kpis: [{ label: 'Programs', value: '22' }, { label: 'Athletics', value: '14' }, { label: 'Clubs', value: '8' }, { label: 'Participants', value: '268' }],
      details: ['14 athletic programs â€” fall/winter/spring', '8 activity clubs and organizations', '268 unique student participants', 'Average program size: 12 students'],
      primaryActionLabel: 'View Programs', backActionLabel: 'Athletics Director',
      primaryActionHref: '/athletics-director-dashboard', backActionHref: '/athletics-director-dashboard', lastUpdated: '8:00 AM' },
    { key: 'clearances', icon: 'CL', title: 'Clearances', status: 'Action Required', statusTone: 'warn',
      mainKpi: '12 clearances outstanding', summary: '9 physicals + 3 permission slips â€” must resolve today.',
      kpis: [{ label: 'Pending', value: '12' }, { label: 'Physicals', value: '9' }, { label: 'Permission', value: '3' }, { label: 'Cleared', value: '268' }],
      details: ['9 student physicals expired or not on file', '3 permission slips not returned', 'All 12 students currently ineligible to compete', 'Families notified via portal'],
      primaryActionLabel: 'Resolve Clearances', backActionLabel: 'Health Office',
      primaryActionHref: '/health-office-dashboard', backActionHref: '/health-office-dashboard', lastUpdated: '8:05 AM' },
    { key: 'schedule', icon: 'EV', title: 'Events & Schedule', status: 'On Track', statusTone: 'good',
      mainKpi: '7 events this week', summary: '3 home, 4 away â€” all logistics confirmed except 1 bus.',
      kpis: [{ label: 'This Week', value: '7' }, { label: 'Home', value: '3' }, { label: 'Away', value: '4' }, { label: 'Transport Confirmed', value: '6' }],
      details: ['3 home events at HCA campus', '4 away events â€” 6 buses confirmed', '1 Friday bus pending Transportation confirmation', 'Venue contacts updated for spring season'],
      primaryActionLabel: 'View Calendar', backActionLabel: 'Transportation',
      primaryActionHref: '/transportation-dashboard', backActionHref: '/transportation-dashboard', lastUpdated: '8:10 AM' },
    { key: 'eligibility', icon: 'EL', title: 'Eligibility Tracking', status: 'Watch', statusTone: 'warn',
      mainKpi: '4 students on academic watch', summary: '4 students below GPA threshold â€” weekly checks.',
      kpis: [{ label: 'On Watch', value: '4' }, { label: 'Ineligible', value: '0' }, { label: 'GPA Threshold', value: '2.0' }, { label: 'Avg GPA', value: '3.1' }],
      details: ['4 students on academic eligibility watch', 'None currently ineligible', 'GPA checked weekly against 2.0 minimum', 'Counselors notified for watch students'],
      primaryActionLabel: 'View Eligibility', backActionLabel: 'Gradebook',
      primaryActionHref: '/gradebook-dashboard', backActionHref: '/gradebook-dashboard', lastUpdated: '7:55 AM' },
    { key: 'facilities', icon: 'FA', title: 'Facilities & Equipment', status: 'Stable', statusTone: 'good',
      mainKpi: 'All fields and gyms operational', summary: 'Equipment inventory current â€” 2 items on order.',
      kpis: [{ label: 'Venues Active', value: '5' }, { label: 'Equipment Issues', value: '2' }, { label: 'On Order', value: '2' }, { label: 'Last Inspection', value: 'April 10' }],
      details: ['Varsity gym, JV gym, 2 fields, track all operational', '2 equipment items on replacement order', 'Last safety inspection: April 10 â€” passed', 'Locker room maintenance scheduled'],
      primaryActionLabel: 'View Facilities', backActionLabel: 'Facilities Dashboard',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:15 AM' },
    { key: 'league', icon: 'LG', title: 'League & CSAA', status: 'Due Soon', statusTone: 'warn',
      mainKpi: 'CSAA submission due April 29', summary: 'Spring schedule draft complete â€” needs AD signature.',
      kpis: [{ label: 'Submission Due', value: 'Apr 29' }, { label: 'Sports Submitting', value: '6' }, { label: 'Draft Status', value: 'Ready' }, { label: 'Signed', value: 'No' }],
      details: ['Spring season schedules for 6 sports', 'Draft submitted internally', 'Awaiting Athletics Director signature', 'CSAA deadline April 29 â€” 3 days remaining'],
      primaryActionLabel: 'Open CSAA Submission', backActionLabel: 'Athletics Director',
      primaryActionHref: '/athletics-director-dashboard', backActionHref: '/athletics-director-dashboard', lastUpdated: '8:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Student participation', title: 'Unique Participants YTD', chip: '268 students (+5%)', trend: PART_TREND },
    { kicker: 'Event volume', title: 'Events Per Month', chip: '14 events in March', trend: EVENT_TREND },
  ],

  activities: [
    'CSAA spring schedule draft submitted for AD review.',
    '12 clearance deficiencies flagged â€” families notified.',
    'Friday away bus confirmation requested from Transportation.',
    'Academic eligibility watch: 4 students flagged.',
    '268 students confirmed active in programs this semester.',
  ],

  quickActions: [
    { label: 'View Calendar', href: '/activities-athletics-dashboard' },
    { label: 'Clearances', href: '/health-office-dashboard' },
    { label: 'Athletics Director', href: '/athletics-director-dashboard' },
    { label: 'Transportation', href: '/transportation-dashboard' },
  ],

  statuses: [
    { label: 'Programs', state: '22 active' },
    { label: 'Clearances', state: '12 pending' },
    { label: 'Events This Week', state: '7 scheduled' },
    { label: 'CSAA Submission', state: 'Due April 29' },
  ],
};

