import { BASE_NOTE } from './_baseData.js';

const SCHED_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 },
  { month: 'Nov', value: 31 }, { month: 'Dec', value: 40 }, { month: 'Jan', value: 52 },
  { month: 'Feb', value: 68 }, { month: 'Mar', value: 74 },
];
const CONFLICT_TREND = [
  { month: 'Aug', value: 8 }, { month: 'Sep', value: 6 }, { month: 'Oct', value: 5 },
  { month: 'Nov', value: 7 }, { month: 'Dec', value: 4 }, { month: 'Jan', value: 6 },
  { month: 'Feb', value: 3 }, { month: 'Mar', value: 2 },
];

export default {
  key: 'scheduling',
  activePath: '/scheduling-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'SC', name: 'Scheduling Office', role: 'Academics â€” Master Schedule & Sections' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Scheduler!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Scheduling widgets currently use template snapshots pending live scheduling service integration.',
  note: 'Certification remains in review until scheduling metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/scheduling/summary/',
  liveDataKey: 'scheduling',
  metrics: [
    { label: 'Sections Built', value: '148', detail: '97% of target â€” 4 sections pending staff.', accent: 'blue' },
    { label: 'Schedule Conflicts', value: '2', detail: 'Down from 8 last month â€” near zero target.', accent: 'emerald' },
    { label: 'Teacher Load', value: '94%', detail: 'Avg 4.7 sections/teacher â€” within policy.', accent: 'gold' },
    { label: 'Room Utilization', value: '89%', detail: '31 of 35 rooms in active use this semester.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Resolve 2 remaining schedule conflicts', detail: 'Period 4 overlap â€” AP Chemistry vs Lab Block.', state: 'Today', tone: 'warn' },
    { title: 'Confirm Fall 2026 section counts', detail: 'Enrollment projections due by May 1.', state: 'This week', tone: 'warn' },
    { title: 'Staff 4 pending sections', detail: 'Math, Science, PE x2 â€” HR coordinating.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Scheduling priorities',

  alerts: [
    { title: 'AP Chemistry conflict unresolved', detail: 'Period 4 lab block overlap â€” needs admin decision.', tone: 'warn' },
    { title: 'Fall 2026 scheduling window opens May 15', detail: 'Prepare enrollment numbers and staff load data.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'sections', icon: 'SE', title: 'Section Management', status: 'On Track', statusTone: 'good',
      mainKpi: '148 sections built (97%)', summary: '4 sections pending staffing â€” conflicts near zero.',
      kpis: [{ label: 'Sections Built', value: '148' }, { label: 'Target', value: '152' }, { label: 'Pending Staff', value: '4' }, { label: 'Conflicts', value: '2' }],
      details: ['148 of 152 target sections active', '4 sections awaiting teacher assignment', '2 unresolved schedule conflicts', 'Section sizes within policy range'],
      primaryActionLabel: 'View Sections', backActionLabel: 'Master Schedule',
      primaryActionHref: '/scheduling-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:00 AM' },
    { key: 'conflicts', icon: 'CF', title: 'Conflict Resolution', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 unresolved conflicts', summary: 'AP Chemistry/Lab Block conflict needs admin decision.',
      kpis: [{ label: 'Open', value: '2' }, { label: 'Resolved YTD', value: '14' }, { label: 'Critical', value: '1' }, { label: 'Auto-resolved', value: '11' }],
      details: ['AP Chemistry vs Lab Block â€” Period 4', 'Teacher period overlap â€” Math Dept', '14 conflicts resolved this semester', '11 resolved by auto-reassignment'],
      primaryActionLabel: 'Resolve Conflicts', backActionLabel: 'View Log',
      primaryActionHref: '/scheduling-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:05 AM' },
    { key: 'teacherLoad', icon: 'TL', title: 'Teacher Load', status: 'Stable', statusTone: 'good',
      mainKpi: '94% load average', summary: 'Staff loads within policy â€” no overload flags.',
      kpis: [{ label: 'Avg Sections', value: '4.7' }, { label: 'Max Policy', value: '6' }, { label: 'Overloaded', value: '0' }, { label: 'Under 4', value: '3' }],
      details: ['Avg 4.7 sections per full-time teacher', 'No teachers exceeding 6-section cap', '3 part-time teachers at 3 sections', 'Prep periods in compliance for all staff'],
      primaryActionLabel: 'View Teacher Loads', backActionLabel: 'HR Dashboard',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '7:55 AM' },
    { key: 'rooms', icon: 'RM', title: 'Room Assignments', status: 'Stable', statusTone: 'good',
      mainKpi: '89% room utilization', summary: '31 of 35 rooms in active use â€” 4 held for special use.',
      kpis: [{ label: 'Rooms Active', value: '31' }, { label: 'Total', value: '35' }, { label: 'Utilization', value: '89%' }, { label: 'Double-Booked', value: '0' }],
      details: ['31 rooms assigned to regular sections', '2 rooms reserved for testing', '1 room in renovation', '1 room designated for special events'],
      primaryActionLabel: 'View Room Map', backActionLabel: 'Facilities',
      primaryActionHref: '/facilities-dashboard', backActionHref: '/facilities-dashboard', lastUpdated: '8:10 AM' },
    { key: 'enrollment', icon: 'EN', title: 'Enrollment Projections', status: 'Planning', statusTone: 'good',
      mainKpi: 'Fall 2026 projections due May 1', summary: 'Enrollment data needed for Fall schedule build.',
      kpis: [{ label: 'Current Enrollment', value: '612' }, { label: 'Fall Projection', value: '628' }, { label: 'New Sections Needed', value: '6' }, { label: 'Data Due', value: 'May 1' }],
      details: ['612 enrolled this semester', 'Fall projection: 628 students (+2.6%)', '6 additional sections needed for fall', 'Admissions data requested by May 1'],
      primaryActionLabel: 'View Projections', backActionLabel: 'Admissions',
      primaryActionHref: '/admissions-dashboard', backActionHref: '/admissions-dashboard', lastUpdated: '7:45 AM' },
    { key: 'reports', icon: 'RP', title: 'Schedule Reports', status: 'Stable', statusTone: 'good',
      mainKpi: 'Current schedule report ready', summary: 'Master schedule export and conflict log current.',
      kpis: [{ label: 'Reports Ready', value: '4' }, { label: 'Sections', value: '148' }, { label: 'Conflicts', value: '2' }, { label: 'Utilization', value: '89%' }],
      details: ['Master schedule PDF generated', 'Conflict log current through April', 'Teacher load summary ready', 'Room utilization report available'],
      primaryActionLabel: 'Export Schedule', backActionLabel: 'View Reports',
      primaryActionHref: '/scheduling-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Section build progress', title: 'Sections Built YTD', chip: '148 of 152', trend: SCHED_TREND },
    { kicker: 'Conflict resolution', title: 'Open Conflicts Over Time', chip: '2 remaining', trend: CONFLICT_TREND },
  ],

  activities: [
    'AP Chemistry conflict escalated for admin decision.',
    'Fall 2026 projection request sent to Admissions.',
    '4 pending sections flagged for HR staffing.',
    'Master schedule export shared with principal.',
    'Room utilization report prepared for board review.',
  ],

  quickActions: [
    { label: 'View Schedule', href: '/scheduling-dashboard' },
    { label: 'Resolve Conflicts', href: '/scheduling-dashboard' },
    { label: 'Teacher Loads', href: '/hr-dashboard' },
    { label: 'Room Map', href: '/facilities-dashboard' },
  ],

  statuses: [
    { label: 'Master Schedule', state: 'Active' },
    { label: 'Open Conflicts', state: '2 pending' },
    { label: 'Room Assignments', state: 'Current' },
    { label: 'Fall Planning', state: 'In progress' },
  ],
};

