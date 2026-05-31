import { BASE_NOTE } from './_baseData.js';

const ROUTE_TREND = [
  { month: 'Aug', value: 8 }, { month: 'Sep', value: 10 }, { month: 'Oct', value: 10 },
  { month: 'Nov', value: 10 }, { month: 'Dec', value: 9 }, { month: 'Jan', value: 10 },
  { month: 'Feb', value: 10 }, { month: 'Mar', value: 11 },
];
const OT_TREND = [
  { month: 'Aug', value: 94 }, { month: 'Sep', value: 96 }, { month: 'Oct', value: 97 },
  { month: 'Nov', value: 95 }, { month: 'Dec', value: 93 }, { month: 'Jan', value: 96 },
  { month: 'Feb', value: 97 }, { month: 'Mar', value: 98 },
];

export default {
  key: 'transportation',
  activePath: '/transportation-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'TR', name: 'Transportation', role: 'Operations â€” Student Transportation' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Transportation!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Transportation widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until transportation metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/transportation/summary/',
  liveDataKey: 'transportation',
  metrics: [
    { label: 'Routes Active', value: '11', detail: 'All 11 morning and afternoon routes operational.', accent: 'emerald' },
    { label: 'Students Riding', value: '184', detail: '30% of enrollment â€” 4 routes with 100% fill.', accent: 'blue' },
    { label: 'On-Time Rate', value: '98%', detail: 'Best month this year â€” 2 minor delays in March.', accent: 'gold' },
    { label: 'Incidents', value: '0', detail: 'Zero incidents this month â€” 6-month clean record.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Confirm Friday field trip buses x3', detail: 'Three teams need transportation â€” contact Athletics.', state: 'Today', tone: 'warn' },
    { title: 'Schedule bus 4 annual inspection', detail: 'Due by May 15 â€” contact mechanic for appointment.', state: 'This week', tone: 'warn' },
    { title: 'Update emergency contact roster', detail: '6 families updated contacts â€” roster sync needed.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Transportation priorities',

  alerts: [
    { title: 'Field trip buses needed Friday â€” 3 teams', detail: 'Athletics notified â€” awaiting headcounts for each team.', tone: 'warn' },
    { title: 'Bus 4 inspection due May 15', detail: 'Annual state inspection â€” mechanic appointment needed.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'routes', icon: 'RT', title: 'Routes', status: 'All Active', statusTone: 'good',
      mainKpi: '11 routes â€” 184 students', summary: 'All routes operational â€” on-time rate 98%.',
      kpis: [{ label: 'Routes', value: '11' }, { label: 'Morning', value: '11' }, { label: 'Afternoon', value: '11' }, { label: 'Students', value: '184' }],
      details: ['11 AM and 11 PM routes running', '184 students assigned to routes', '4 routes at 100% capacity', 'Route maps updated for spring'],
      primaryActionLabel: 'View Routes', backActionLabel: 'Student Roster',
      primaryActionHref: '/transportation-dashboard', backActionHref: '/transportation-dashboard', lastUpdated: '7:45 AM' },
    { key: 'fleet', icon: 'FL', title: 'Fleet Status', status: 'Watch', statusTone: 'warn',
      mainKpi: '6 buses â€” 1 inspection due', summary: 'All buses operational â€” Bus 4 inspection due May 15.',
      kpis: [{ label: 'Fleet Size', value: '6' }, { label: 'Operational', value: '6' }, { label: 'Inspection Due', value: '1' }, { label: 'Last Maint.', value: 'April 2' }],
      details: ['6 buses all operational', 'Bus 4 annual inspection due May 15', 'Routine maintenance completed April 2', '1 minor repair scheduled for this week'],
      primaryActionLabel: 'Fleet Status', backActionLabel: 'Maintenance Log',
      primaryActionHref: '/transportation-dashboard', backActionHref: '/transportation-dashboard', lastUpdated: '8:00 AM' },
    { key: 'drivers', icon: 'DR', title: 'Drivers', status: 'Stable', statusTone: 'good',
      mainKpi: '7 licensed drivers on roster', summary: 'All drivers current on CDL, background check, and training.',
      kpis: [{ label: 'Drivers', value: '7' }, { label: 'CDL Current', value: '7' }, { label: 'BG Check', value: '7' }, { label: 'Training Due', value: '1' }],
      details: ['7 drivers on roster â€” all CDL current', 'Background checks current for all', '1 annual safety training due in June', 'Substitute driver available as needed'],
      primaryActionLabel: 'Driver Records', backActionLabel: 'HR Dashboard',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:05 AM' },
    { key: 'fieldTrips', icon: 'FT', title: 'Field Trips', status: 'Action Required', statusTone: 'warn',
      mainKpi: 'Friday: 3 buses needed', summary: 'Athletics games â€” headcounts needed to confirm buses.',
      kpis: [{ label: 'This Week', value: '3' }, { label: 'Buses Needed', value: '3' }, { label: 'Confirmed', value: '0' }, { label: 'Headcount', value: 'Pending' }],
      details: ['3 away games Friday â€” all need buses', 'Athletics to confirm headcounts today', 'Buses available â€” pending student counts', 'Departure times: 2:30, 3:00, 3:30 PM'],
      primaryActionLabel: 'Manage Field Trips', backActionLabel: 'Athletics',
      primaryActionHref: '/activities-athletics-dashboard', backActionHref: '/activities-athletics-dashboard', lastUpdated: '8:10 AM' },
    { key: 'safety', icon: 'SF', title: 'Safety & Incidents', status: 'Clean', statusTone: 'good',
      mainKpi: 'Zero incidents â€” 6-month record', summary: 'Clean safety record â€” all drivers compliant.',
      kpis: [{ label: 'Incidents', value: '0' }, { label: 'Clean Streak', value: '6 months' }, { label: 'Complaints', value: '0' }, { label: 'Near Misses', value: '0' }],
      details: ['6 consecutive months â€” zero incidents', 'No parent complaints this semester', 'Pre-trip inspection completed daily', 'Safety drills completed Q1'],
      primaryActionLabel: 'Safety Log', backActionLabel: 'Safety Dashboard',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:15 AM' },
    { key: 'contacts', icon: 'CN', title: 'Emergency Contacts', status: 'Watch', statusTone: 'warn',
      mainKpi: '6 contact updates pending sync', summary: '6 families updated contacts â€” roster needs refresh.',
      kpis: [{ label: 'Updates Pending', value: '6' }, { label: 'Total Riders', value: '184' }, { label: 'Contacts Current', value: '178' }, { label: 'Last Sync', value: 'April 14' }],
      details: ['6 families updated emergency contacts', 'Roster sync needed from student records', 'Last sync: April 14', 'Medical alert cards printed for all riders'],
      primaryActionLabel: 'Sync Contacts', backActionLabel: 'Student Records',
      primaryActionHref: '/transportation-dashboard', backActionHref: '/transportation-dashboard', lastUpdated: '8:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Route coverage', title: 'Active Routes Over Time', chip: '11 routes active', trend: ROUTE_TREND },
    { kicker: 'Punctuality', title: 'On-Time Rate (%)', chip: '98% â€” best month', trend: OT_TREND },
  ],

  activities: [
    'Friday field trip request received â€” 3 buses needed for Athletics.',
    'Bus 4 annual inspection scheduled for May 12.',
    '6 emergency contact updates queued for roster sync.',
    'Route 7 minor delay this morning â€” resolved by 8:10 AM.',
    'Pre-trip inspections completed for all 6 buses.',
  ],

  quickActions: [
    { label: 'View Routes', href: '/transportation-dashboard' },
    { label: 'Fleet Status', href: '/transportation-dashboard' },
    { label: 'Field Trips', href: '/activities-athletics-dashboard' },
    { label: 'Safety Log', href: '/safety-security-dashboard' },
  ],

  statuses: [
    { label: 'Morning Routes', state: 'All running' },
    { label: 'Fleet', state: '6 operational' },
    { label: 'Friday Buses', state: 'Pending confirm' },
    { label: 'Safety Record', state: '6-month clean' },
  ],
};

