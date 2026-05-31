import { BASE_NOTE } from './_baseData.js';

const ENROLLMENT_TREND = [
  { month: 'Aug', value: 365 },
  { month: 'Sep', value: 374 },
  { month: 'Oct', value: 382 },
  { month: 'Nov', value: 391 },
  { month: 'Dec', value: 397 },
  { month: 'Jan', value: 403 },
  { month: 'Feb', value: 409 },
  { month: 'Mar', value: 412 },
];

const REVENUE_TREND = [
  { month: 'Aug', value: 240 },
  { month: 'Sep', value: 410 },
  { month: 'Oct', value: 695 },
  { month: 'Nov', value: 980 },
  { month: 'Dec', value: 1410 },
  { month: 'Jan', value: 1960 },
  { month: 'Feb', value: 2520 },
  { month: 'Mar', value: 3100 },
];

export default {
  key: 'board',
  activePath: '/board',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'BD', name: 'Board of Directors', role: 'Governance â€” Strategic Oversight' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Board!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/board/summary/',
  liveDataKey: 'board',

  metrics: [
    { label: 'Enrollment', value: '412', detail: '+4% vs last year â€” tracking ahead of plan.', accent: 'blue' },
    { label: 'Revenue Collected', value: '$3.1M', detail: '+6% YTD â€” collection cadence strong.', accent: 'emerald' },
    { label: 'Retention Rate', value: '92%', detail: '+2% vs prior year â€” returning families up.', accent: 'gold' },
    { label: 'Mission Engagement', value: '81%', detail: 'Composite of service, chapel, and mission programs.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Approve Q2 strategic plan update', detail: 'Finance + Mission committees aligned. Vote scheduled this session.', state: 'This session', tone: 'warn' },
    { title: 'Review enrollment goal pacing', detail: '412 of 450 enrolled â€” on track for 91% of plan.', state: 'Today', tone: 'warn' },
    { title: 'Confirm spring fundraising scope', detail: 'Advancement target $250K â€” committee endorsement required.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Board priorities',

  alerts: [
    { title: 'Grade-level retention watch', detail: 'Two grade levels tracking below 88% retention â€” admissions follow-up underway.', tone: 'warn' },
    { title: 'Capital reserve review due', detail: 'Annual reserve assessment scheduled for May session.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'enrollment', icon: 'EN', title: 'Enrollment', status: 'Stable', statusTone: 'good',
      mainKpi: '412 of 450 (91%)', summary: 'Enrollment pacing strong â€” 4% ahead of last year through March.',
      kpis: [{ label: 'Enrolled', value: '412' }, { label: 'Goal', value: '450' }, { label: 'YoY change', value: '+4%' }, { label: 'Pipeline', value: '54 apps' }],
      details: ['New student enrollment up 12 vs prior year', 'Re-enrollment confirmed for 312 families', 'Wait list active in 3 grade levels', 'Open House conversion 28%'],
      primaryActionLabel: 'Open Admissions', backActionLabel: 'View Pipeline',
      primaryActionHref: '/admissions', backActionHref: '/admissions/pipeline', lastUpdated: '8:30 AM' },
    { key: 'revenue', icon: 'RV', title: 'Revenue & Finance', status: 'Stable', statusTone: 'good',
      mainKpi: '$3.1M of $3.3M (94%)', summary: 'Revenue collection ahead of plan; AR aging steady.',
      kpis: [{ label: 'Collected YTD', value: '$3.1M' }, { label: 'Target', value: '$3.3M' }, { label: 'YoY', value: '+6%' }, { label: 'Outstanding AR', value: '$210K' }],
      details: ['Tuition collection rate 94%', 'Auxiliary revenue tracking +8%', 'Aid disbursements on schedule', 'Q3 forecast within plan'],
      primaryActionLabel: 'Open Finance', backActionLabel: 'View Reports',
      primaryActionHref: '/finance', backActionHref: '/reports', lastUpdated: '8:25 AM' },
    { key: 'retention', icon: 'RT', title: 'Retention & Health', status: 'Watch', statusTone: 'warn',
      mainKpi: '92% returning', summary: 'Retention strong overall; two grade levels need attention.',
      kpis: [{ label: 'Retention rate', value: '92%' }, { label: 'YoY', value: '+2%' }, { label: 'At-risk grades', value: '2' }, { label: 'Health index', value: '87' }],
      details: ['Grades 9 and 11 below 88% retention threshold', 'Family satisfaction survey at 4.6/5', 'Counselor outreach in flight for 12 families', 'Annual retention report due May'],
      primaryActionLabel: 'View Retention Report', backActionLabel: 'Open Counseling',
      primaryActionHref: '/reports', backActionHref: '/counseling', lastUpdated: '7:55 AM' },
    { key: 'mission', icon: 'MS', title: 'Mission & Engagement', status: 'Stable', statusTone: 'good',
      mainKpi: '81% engagement composite', summary: 'Service, chapel, and mission programs running ahead of plan.',
      kpis: [{ label: 'Service hours', value: '2,340' }, { label: 'Chapel attendance', value: '89%' }, { label: 'Mission projects', value: '7' }, { label: 'Engagement index', value: '81' }],
      details: ['Service hours +112 this week', 'Chapel attendance steady at 89%', '7 active mission service projects', 'Spring outreach week scheduled May 14'],
      primaryActionLabel: 'Open Spiritual Life', backActionLabel: 'Service Hours',
      primaryActionHref: '/spiritual-life', backActionHref: '/service-hours', lastUpdated: '8:05 AM' },
    { key: 'governance', icon: 'GV', title: 'Governance & Compliance', status: 'Stable', statusTone: 'good',
      mainKpi: 'All filings current', summary: 'Annual filings, audits, and accreditation documents all up to date.',
      kpis: [{ label: 'Open committee items', value: '3' }, { label: 'Filings current', value: 'All' }, { label: 'Audit status', value: 'Clean' }, { label: 'Policy reviews', value: '2 due' }],
      details: ['Strategic plan revision in committee', 'External audit completed Feb â€” clean opinion', 'Two policies due for triennial review', 'Accreditation site visit scheduled fall'],
      primaryActionLabel: 'Governance Detail', backActionLabel: 'Open Reports',
      primaryActionHref: '/reports', backActionHref: '/system-status', lastUpdated: '8:00 AM' },
    { key: 'communications', icon: 'CO', title: 'Board Communications', status: 'Stable', statusTone: 'good',
      mainKpi: '4 updates this week', summary: 'Communications cadence on schedule; family newsletter sent Monday.',
      kpis: [{ label: 'Updates this week', value: '4' }, { label: 'Family newsletter', value: 'Sent Mon' }, { label: 'Board minutes', value: 'Posted' }, { label: 'Press inquiries', value: '0' }],
      details: ['Family newsletter delivered Monday morning', 'Board meeting minutes posted to portal', 'Annual report draft circulating', 'Spring gala save-the-date in development'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'View Calendar',
      primaryActionHref: '/communications', backActionHref: '/board', lastUpdated: '7:45 AM' },
  ],

  trendPanels: [
    { kicker: 'Enrollment trend', title: 'Current year vs prior year', chip: '8 months YTD', trend: ENROLLMENT_TREND },
    { kicker: 'Revenue trend', title: 'Collected revenue YTD ($K)', chip: '+6% vs prior', trend: REVENUE_TREND },
  ],

  activityKicker: 'Board activity',
  activityTitle: 'Recent governance events',
  activities: [
    'Q2 strategic plan draft circulated to committees.',
    'External audit final report received â€” clean opinion.',
    'Enrollment committee reviewed grade 9/11 retention plan.',
    'Advancement committee endorsed spring fundraising scope.',
    'Annual report draft posted for committee review.',
  ],

  quickActions: [
    { title: 'Open Reports', eyebrow: 'Quick action', description: 'Review board reports, audits, and snapshot summaries.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['board'] },
    { title: 'View Finance', eyebrow: 'Quick action', description: 'Open finance dashboard for revenue and AR detail.', actionLabel: 'Open Finance', href: '/finance', allowedRoles: ['board'] },
    { title: 'View Admissions', eyebrow: 'Quick action', description: 'Review enrollment pipeline and conversion metrics.', actionLabel: 'Open Admissions', href: '/admissions', allowedRoles: ['board'] },
    { title: 'Spiritual Life', eyebrow: 'Quick action', description: 'Review chapel, service, and mission engagement.', actionLabel: 'Open Spiritual Life', href: '/spiritual-life', allowedRoles: ['board'] },
  ],

  statusTitle: 'Board workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Reports Pipeline', state: 'Current' },
    { label: 'Audit Status', state: 'Clean opinion' },
    { label: 'Filings', state: 'All current' },
    { label: 'Board Portal', state: 'Online' },
  ],
};
