const WO_TREND = [
  { month: 'Aug', value: 14 }, { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 },
  { month: 'Nov', value: 19 }, { month: 'Dec', value: 24 }, { month: 'Jan', value: 21 },
  { month: 'Feb', value: 17 }, { month: 'Mar', value: 23 },
];
const CLOSE_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 16 }, { month: 'Oct', value: 19 },
  { month: 'Nov', value: 17 }, { month: 'Dec', value: 22 }, { month: 'Jan', value: 20 },
  { month: 'Feb', value: 16 }, { month: 'Mar', value: 21 },
];

export default {
  key: 'facilities',
  activePath: '/facilities-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'FM', name: 'Facilities Management', role: 'Operations — Facilities & Maintenance' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Facilities!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Facilities widgets currently use template snapshots pending live facilities service integration.',
  note: 'Certification remains in review until facilities metrics are sourced from canonical runtime endpoints.',

  metrics: [
    { label: 'Open Work Orders', value: '8', detail: '3 urgent, 5 standard — all assigned.', accent: 'gold' },
    { label: 'Completed Today', value: '3', detail: 'HVAC filter, hallway light, gym door latch.', accent: 'emerald' },
    { label: 'Preventive Maint.', value: '94%', detail: 'Spring PM schedule 94% complete — 2 deferred.', accent: 'blue' },
    { label: 'Rooms Ready', value: '35/35', detail: 'All classrooms and common areas cleared for use.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Repair gym bleacher section B', detail: 'Urgent — blocked off for safety. Vendor scheduled noon.', state: 'Today', tone: 'warn' },
    { title: 'Complete 2 deferred PM tasks', detail: 'Roof drain and exterior lighting — schedule this week.', state: 'This week', tone: 'warn' },
    { title: 'Submit annual fire inspection report', detail: 'Inspection complete — documentation due to admin April 30.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Facilities priorities',

  alerts: [
    { title: 'Gym bleacher section B unsafe — blocked', detail: 'Vendor repair scheduled noon today — area cordoned off.', tone: 'warn' },
    { title: 'Annual fire inspection report due April 30', detail: 'Inspection passed — written report needed for files.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'workOrders', icon: 'WO', title: 'Work Orders', status: 'Watch', statusTone: 'warn',
      mainKpi: '8 open orders — 3 urgent', summary: 'All work orders assigned — bleacher repair urgent.',
      kpis: [{ label: 'Open', value: '8' }, { label: 'Urgent', value: '3' }, { label: 'Standard', value: '5' }, { label: 'Completed Today', value: '3' }],
      details: ['Bleacher section B: vendor noon today', 'Library HVAC: staff assigned', 'Exterior lighting: scheduled Thursday', '3 completed this morning'],
      primaryActionLabel: 'View Work Orders', backActionLabel: 'Create Order',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:00 AM' },
    { key: 'preventive', icon: 'PM', title: 'Preventive Maint.', status: 'On Track', statusTone: 'good',
      mainKpi: '94% spring PM complete', summary: '2 deferred tasks — roof drain and exterior lights.',
      kpis: [{ label: 'PM Complete', value: '94%' }, { label: 'Tasks Done', value: '32' }, { label: 'Deferred', value: '2' }, { label: 'Next Major PM', value: 'June' }],
      details: ['32 of 34 spring PM tasks complete', 'Roof drain inspection deferred — scheduling', 'Exterior pathway lighting on hold', 'Summer PM planning begins May 1'],
      primaryActionLabel: 'PM Schedule', backActionLabel: 'View History',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:05 AM' },
    { key: 'rooms', icon: 'RM', title: 'Room Readiness', status: 'All Clear', statusTone: 'good',
      mainKpi: '35/35 rooms ready', summary: 'All classrooms and common areas cleared for occupancy.',
      kpis: [{ label: 'Rooms Ready', value: '35' }, { label: 'Total', value: '35' }, { label: 'Under Repair', value: '0' }, { label: 'Inspected', value: '35' }],
      details: ['All 35 rooms cleared and ready', 'Daily walk-through completed at 7 AM', 'No rooms under repair', 'Weekly deep-clean schedule current'],
      primaryActionLabel: 'Room Status', backActionLabel: 'Scheduling',
      primaryActionHref: '/scheduling-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:10 AM' },
    { key: 'inspection', icon: 'IS', title: 'Inspections', status: 'Due', statusTone: 'warn',
      mainKpi: 'Fire inspection report due April 30', summary: 'Inspection passed — written report needed.',
      kpis: [{ label: 'Last Inspection', value: 'April 18' }, { label: 'Result', value: 'Passed' }, { label: 'Report Due', value: 'April 30' }, { label: 'Next Inspection', value: 'Oct 2026' }],
      details: ['Annual fire safety inspection: April 18 — passed', 'Written report due to admin: April 30', 'No corrective actions required', 'Next fire inspection: October 2026'],
      primaryActionLabel: 'Submit Report', backActionLabel: 'Compliance',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:15 AM' },
    { key: 'vendors', icon: 'VN', title: 'Vendors & Contracts', status: 'Stable', statusTone: 'good',
      mainKpi: '4 active vendor contracts', summary: 'All contracts current — bleacher vendor confirmed today.',
      kpis: [{ label: 'Active Contracts', value: '4' }, { label: 'Due for Renewal', value: '1' }, { label: 'Scheduled Today', value: '1' }, { label: 'Spend YTD', value: '$12.4K' }],
      details: ['Bleacher repair vendor confirmed noon', 'HVAC service contract renews June 1', 'Landscaping contract active through September', 'Cleaning service weekly — current'],
      primaryActionLabel: 'Manage Vendors', backActionLabel: 'View Contracts',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:20 AM' },
    { key: 'safety', icon: 'SF', title: 'Safety & Access', status: 'Stable', statusTone: 'good',
      mainKpi: 'All access systems operational', summary: 'Keycard and camera systems nominal — 1 door flagged.',
      kpis: [{ label: 'Access Points', value: '12' }, { label: 'Operational', value: '12' }, { label: 'Camera Feeds', value: '24' }, { label: 'Door Issues', value: '0' }],
      details: ['All 12 access control points operational', '24 camera feeds active and recording', 'Bleacher area barrier placed for safety', 'Lock battery replacement: 2 scheduled'],
      primaryActionLabel: 'View Safety', backActionLabel: 'Safety Dashboard',
      primaryActionHref: '/safety-security-dashboard', backActionHref: '/safety-security-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Work order volume', title: 'Open Work Orders Per Month', chip: '8 open currently', trend: WO_TREND },
    { kicker: 'Completion rate', title: 'Work Orders Closed Per Month', chip: '21 closed in March', trend: CLOSE_TREND },
  ],

  activities: [
    'Bleacher section B blocked — vendor repair scheduled noon.',
    '3 work orders completed this morning (HVAC, lighting, door).',
    'Fire inspection report drafted for admin submission.',
    'Spring PM schedule 94% complete — 2 tasks remain.',
    'All 35 classrooms confirmed ready for daily use.',
  ],

  quickActions: [
    { label: 'Work Orders', href: '/facilities-dashboard' },
    { label: 'PM Schedule', href: '/facilities-dashboard' },
    { label: 'Safety Systems', href: '/safety-security-dashboard' },
    { label: 'Room Status', href: '/scheduling-dashboard' },
  ],

  statuses: [
    { label: 'Work Orders', state: '8 open (3 urgent)' },
    { label: 'PM Schedule', state: '94% complete' },
    { label: 'Room Readiness', state: 'All 35 clear' },
    { label: 'Fire Inspection', state: 'Report due Apr 30' },
  ],
};
