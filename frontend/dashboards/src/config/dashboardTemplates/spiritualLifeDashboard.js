import { BASE_NOTE } from './_baseData.js';

const CHAPEL_TREND = [
  { month: 'Sep', value: 84 }, { month: 'Oct', value: 86 }, { month: 'Nov', value: 87 },
  { month: 'Dec', value: 88 }, { month: 'Jan', value: 88 }, { month: 'Feb', value: 89 }, { month: 'Mar', value: 89 },
];
const SERVICE_TREND = [
  { month: 'Sep', value: 410 }, { month: 'Oct', value: 580 }, { month: 'Nov', value: 760 },
  { month: 'Dec', value: 1180 }, { month: 'Jan', value: 1620 }, { month: 'Feb', value: 1980 }, { month: 'Mar', value: 2340 },
];

export default {
  key: 'spiritualLife',
  activePath: '/spiritual-life',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'CH', name: 'Chaplain', role: 'Spiritual Life — Formation & Pastoral Care' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Chaplain!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Chapel Attendance', value: '89%', detail: 'Strong this week — above 4-week average.', accent: 'emerald' },
    { label: 'Service Hours Logged', value: '2,340', detail: '+112 this week — pacing toward 3,000 goal.', accent: 'blue' },
    { label: 'Care Referrals', value: '6', detail: 'Active pastoral care cases this week.', accent: 'gold' },
    { label: 'Mentoring Follow-Ups', value: '4', detail: 'Pending check-ins this week.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Complete 4 mentoring follow-ups', detail: 'Check-ins scheduled this week — confirm meeting times.', state: 'This week', tone: 'warn' },
    { title: 'Plan spring outreach week', detail: 'May 14 service week — coordinate logistics with Student Life.', state: 'This week', tone: 'warn' },
    { title: 'Distribute weekly devotion', detail: 'Friday family devotion ready for review.', state: 'Friday', tone: 'warn' },
  ],
  prioritiesTitle: 'Pastoral priorities',

  alerts: [
    { title: '6 active care referrals', detail: 'Pastoral care caseload steady — counselor coordination current.', tone: 'warn' },
    { title: 'Mentoring follow-up backlog', detail: '4 students need pastoral check-ins before Friday.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'chapel', icon: 'CH', title: 'Chapel & Worship', status: 'Stable', statusTone: 'good',
      mainKpi: '89% attendance', summary: 'Chapel attendance above 4-week average — engagement strong.',
      kpis: [{ label: 'Attendance %', value: '89%' }, { label: '4-week avg', value: '88%' }, { label: 'Speakers booked', value: '6' }, { label: 'Worship team', value: 'Confirmed' }],
      details: ['89% chapel attendance this week', 'Spring speaker series confirmed through May', 'Worship team rehearsal Tuesday', 'Special chapel for spring break Friday'],
      primaryActionLabel: 'Open Chapel Console', backActionLabel: 'Speaker Schedule',
      primaryActionHref: '/spiritual-life', backActionHref: '/spiritual-life', lastUpdated: '8:30 AM' },
    { key: 'service', icon: 'SV', title: 'Service Hours', status: 'Stable', statusTone: 'good',
      mainKpi: '2,340 of 3,000 hours (78%)', summary: 'Service hours pacing ahead of schedule for annual goal.',
      kpis: [{ label: 'Logged YTD', value: '2,340' }, { label: 'Goal', value: '3,000' }, { label: 'Weekly add', value: '+112' }, { label: 'Active projects', value: '7' }],
      details: ['2,340 of 3,000 annual service hours logged', '+112 hours this week', '7 active service projects', 'Spring outreach week scheduled May 14'],
      primaryActionLabel: 'Open Service Hours', backActionLabel: 'Project Sign-Ups',
      primaryActionHref: '/service-hours', backActionHref: '/spiritual-life', lastUpdated: '8:20 AM' },
    { key: 'care', icon: 'CR', title: 'Pastoral Care', status: 'Watch', statusTone: 'warn',
      mainKpi: '6 active referrals', summary: 'Care load steady. Coordination with counseling current.',
      kpis: [{ label: 'Active referrals', value: '6' }, { label: 'Closed MTD', value: '4' }, { label: 'Family contacts', value: '12' }, { label: 'Counselor handoffs', value: '2' }],
      details: ['6 active pastoral care cases', '4 cases closed this month', '12 family contacts logged this week', '2 cases handed off to counseling team'],
      primaryActionLabel: 'Open Care Console', backActionLabel: 'Counseling Coord.',
      primaryActionHref: '/spiritual-life', backActionHref: '/counseling', lastUpdated: '8:00 AM' },
    { key: 'mentoring', icon: 'MN', title: 'Mentoring', status: 'Watch', statusTone: 'warn',
      mainKpi: '4 follow-ups pending', summary: 'Mentoring program healthy — follow-up checks needed this week.',
      kpis: [{ label: 'Active mentor pairs', value: '34' }, { label: 'Follow-ups pending', value: '4' }, { label: 'Sessions this week', value: '12' }, { label: 'New requests', value: '2' }],
      details: ['34 active mentor / mentee pairs', '4 follow-up check-ins pending this week', '12 mentoring sessions held this week', '2 new mentoring requests pending pairing'],
      primaryActionLabel: 'Mentoring Console', backActionLabel: 'Pairing Queue',
      primaryActionHref: '/spiritual-life', backActionHref: '/spiritual-life', lastUpdated: '7:55 AM' },
    { key: 'devotions', icon: 'DV', title: 'Devotions & Formation', status: 'Stable', statusTone: 'good',
      mainKpi: 'Daily devotion on schedule', summary: 'Daily devotion plan running. Family devotion publishes Friday.',
      kpis: [{ label: 'Daily devotions', value: '5/5' }, { label: 'Family devotion', value: 'Fri' }, { label: 'Bible study groups', value: '8' }, { label: 'Formation classes', value: '3' }],
      details: ['Daily devotions delivered every morning', 'Family devotion publishes Friday afternoon', '8 student-led Bible study groups active', '3 formation classes offered this term'],
      primaryActionLabel: 'Devotion Library', backActionLabel: 'Publishing Queue',
      primaryActionHref: '/spiritual-life', backActionHref: '/communications', lastUpdated: '7:30 AM' },
    { key: 'outreach', icon: 'OU', title: 'Outreach & Missions', status: 'Stable', statusTone: 'good',
      mainKpi: 'Spring outreach May 14', summary: 'Mission planning on schedule. Logistics coordination active.',
      kpis: [{ label: 'Mission projects', value: '7' }, { label: 'Spring outreach', value: 'May 14' }, { label: 'Volunteers', value: '64' }, { label: 'Partner orgs', value: '4' }],
      details: ['7 active mission service projects', 'Spring outreach week scheduled May 14–18', '64 student volunteers signed up', '4 community partner organizations confirmed'],
      primaryActionLabel: 'Outreach Console', backActionLabel: 'Volunteer List',
      primaryActionHref: '/spiritual-life', backActionHref: '/service-hours', lastUpdated: '7:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Chapel attendance trend', title: 'Chapel attendance % by month', chip: 'Above target', trend: CHAPEL_TREND },
    { kicker: 'Service hours trend', title: 'Cumulative service hours YTD', chip: '+112 this week', trend: SERVICE_TREND },
  ],

  activityKicker: 'Spiritual life activity',
  activityTitle: 'Recent pastoral events',
  activities: [
    'Daily devotion delivered to all students.',
    'Spring outreach week confirmed for May 14.',
    '12 mentoring sessions completed this week.',
    'Service project at local food bank logged 36 hours.',
    'Family devotion drafted and ready for Friday.',
  ],

  quickActions: [
    { title: 'Service Hours', eyebrow: 'Quick action', description: 'Review and approve student service hour entries.', actionLabel: 'Open Service Hours', href: '/service-hours', allowedRoles: ['spiritualLife'] },
    { title: 'Counseling', eyebrow: 'Quick action', description: 'Coordinate care handoffs with counseling team.', actionLabel: 'Open Counseling', href: '/counseling', allowedRoles: ['spiritualLife'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Publish family devotion and pastoral updates.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['spiritualLife'] },
    { title: 'Open Spiritual Life', eyebrow: 'Quick action', description: 'Return to the Spiritual Life command center.', actionLabel: 'Open Spiritual Life', href: '/spiritual-life', allowedRoles: ['spiritualLife'] },
  ],

  statusTitle: 'Spiritual Life workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Chapel Schedule', state: 'Confirmed' },
    { label: 'Service Hours Tracker', state: 'Synced' },
    { label: 'Devotion Pipeline', state: 'On schedule' },
    { label: 'Care Coordination', state: 'Current' },
  ],
};
