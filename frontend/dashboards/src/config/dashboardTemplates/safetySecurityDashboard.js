const INC_TREND = [
  { month: 'Aug', value: 2 }, { month: 'Sep', value: 3 }, { month: 'Oct', value: 1 },
  { month: 'Nov', value: 2 }, { month: 'Dec', value: 1 }, { month: 'Jan', value: 2 },
  { month: 'Feb', value: 1 }, { month: 'Mar', value: 0 },
];
const DRILL_TREND = [
  { month: 'Aug', value: 1 }, { month: 'Sep', value: 1 }, { month: 'Oct', value: 1 },
  { month: 'Nov', value: 1 }, { month: 'Dec', value: 1 }, { month: 'Jan', value: 1 },
  { month: 'Feb', value: 1 }, { month: 'Mar', value: 2 },
];

export default {
  key: 'safetySecurity',
  activePath: '/safety-security-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'SS', name: 'Safety & Security', role: 'Operations â€” Campus Safety & Emergency Management' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Safety Team!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Safety and security widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until safety and security metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/safetySecurity/summary/',
  liveDataKey: 'safetySecurity',
  metrics: [
    { label: 'Incidents Today', value: '0', detail: 'Zero incidents â€” clean start to the day.', accent: 'emerald' },
    { label: 'Open Reports', value: '1', detail: '1 minor property incident from last week â€” in review.', accent: 'gold' },
    { label: 'Drills Completed', value: '9/10', detail: '9 of 10 required drills complete â€” lockdown due May.', accent: 'blue' },
    { label: 'System Status', value: 'Nominal', detail: 'All cameras, access control, and alarms operational.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Schedule May lockdown drill', detail: 'Final required drill â€” coordinate with admin and staff.', state: 'This week', tone: 'warn' },
    { title: 'Close open property incident report', detail: 'Admin review complete â€” close report and archive.', state: 'Today', tone: 'nominal' },
    { title: 'Visitor system annual audit', detail: 'Review visitor log completeness and badge practices.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Safety priorities',

  alerts: [
    { title: 'Lockdown drill not yet scheduled for May', detail: 'Remaining required drill â€” contact admin to schedule.', tone: 'warn' },
    { title: '1 open property incident report', detail: 'Minor vandalism â€” admin review done, ready to close.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'incidents', icon: 'IC', title: 'Incidents', status: 'Clear', statusTone: 'good',
      mainKpi: '0 incidents today â€” 1 open from last week', summary: 'Clean day â€” 1 prior incident ready for closure.',
      kpis: [{ label: 'Today', value: '0' }, { label: 'Open Reports', value: '1' }, { label: 'Month to Date', value: '0' }, { label: 'YTD Total', value: '12' }],
      details: ['Zero incidents today', '1 property incident from April 14 in review', 'March: zero incidents â€” best month of year', 'YTD total: 12 minor incidents'],
      primaryActionLabel: 'Incident Log', backActionLabel: 'Reports',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:00 AM' },
    { key: 'access', icon: 'AC', title: 'Access Control', status: 'Nominal', statusTone: 'good',
      mainKpi: 'All 12 access points operational', summary: 'Keycard and door systems nominal â€” zero alerts.',
      kpis: [{ label: 'Access Points', value: '12' }, { label: 'Operational', value: '12' }, { label: 'Alerts', value: '0' }, { label: 'Last Audit', value: 'April 1' }],
      details: ['All 12 keycard access points active', '3 main campus entries monitored', 'Visitor check-in kiosk operational', 'Monthly audit completed April 1'],
      primaryActionLabel: 'Access Log', backActionLabel: 'Visitor System',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:05 AM' },
    { key: 'cameras', icon: 'CM', title: 'Cameras & Alarms', status: 'Nominal', statusTone: 'good',
      mainKpi: '24/24 cameras active', summary: 'All camera feeds and alarms functioning normally.',
      kpis: [{ label: 'Cameras', value: '24' }, { label: 'Active', value: '24' }, { label: 'Alarms', value: '8' }, { label: 'Issues', value: '0' }],
      details: ['24 cameras active and recording', 'Storage: 30-day rolling retention', '8 alarm zones all armed and functional', 'Last system test: April 10'],
      primaryActionLabel: 'Camera Feeds', backActionLabel: 'System Status',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:10 AM' },
    { key: 'drills', icon: 'DR', title: 'Emergency Drills', status: 'Almost Complete', statusTone: 'warn',
      mainKpi: '9/10 required drills done', summary: 'Lockdown drill remaining â€” schedule for May.',
      kpis: [{ label: 'Completed', value: '9' }, { label: 'Required', value: '10' }, { label: 'Remaining', value: '1' }, { label: 'Type Due', value: 'Lockdown' }],
      details: ['9 of 10 state-required drills completed', 'Fire drills: 4/4', 'Evacuation drills: 3/3', 'Lockdown drill: 1 remaining â€” schedule May'],
      primaryActionLabel: 'Drill Schedule', backActionLabel: 'Compliance',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:15 AM' },
    { key: 'visitors', icon: 'VS', title: 'Visitor Management', status: 'Stable', statusTone: 'good',
      mainKpi: '18 visitors logged today', summary: 'Check-in system active â€” all visitors badged.',
      kpis: [{ label: 'Today', value: '18' }, { label: 'Badged', value: '18' }, { label: 'Avg Daily', value: '14' }, { label: 'Incidents', value: '0' }],
      details: ['18 visitors logged this morning', 'All visitors badged via kiosk', 'Background screening active for repeat visitors', 'Annual visitor log audit due this week'],
      primaryActionLabel: 'Visitor Log', backActionLabel: 'Reports',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:20 AM' },
    { key: 'emergency', icon: 'EM', title: 'Emergency Plans', status: 'Current', statusTone: 'good',
      mainKpi: 'Emergency plans current', summary: 'All plans reviewed and filed â€” next review Q3.',
      kpis: [{ label: 'Plans Filed', value: '6' }, { label: 'Last Review', value: 'Jan 2026' }, { label: 'Next Review', value: 'July 2026' }, { label: 'Diocese Filed', value: 'Yes' }],
      details: ['6 emergency response plans current', 'Reviewed and updated January 2026', 'Filed with diocese and local fire dept', 'Next full review: July 2026'],
      primaryActionLabel: 'Emergency Plans', backActionLabel: 'Compliance',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Incident volume', title: 'Monthly Incidents', chip: '0 in March', trend: INC_TREND },
    { kicker: 'Drill compliance', title: 'Drills Completed Per Month', chip: '9/10 YTD', trend: DRILL_TREND },
  ],

  activities: [
    'Zero incidents today â€” clean opening.',
    'Property incident report from April 14 ready for closure.',
    'May lockdown drill request sent to principal for scheduling.',
    'Annual visitor log audit initiated.',
    '18 visitors logged and badged this morning.',
  ],

  quickActions: [
    { label: 'Incident Log', href: '/safety-security-dashboard' },
    { label: 'Camera Feeds', href: '/safety-security-dashboard' },
    { label: 'Drill Schedule', href: '/safety-security-dashboard' },
    { label: 'Visitor Log', href: '/safety-security-dashboard' },
  ],

  statuses: [
    { label: 'Campus Status', state: 'Secure' },
    { label: 'Open Incidents', state: '1 (minor)' },
    { label: 'Drills', state: '9/10 complete' },
    { label: 'Systems', state: 'All nominal' },
  ],
};

