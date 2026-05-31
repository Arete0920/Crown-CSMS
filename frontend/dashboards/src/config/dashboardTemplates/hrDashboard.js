import { BASE_NOTE } from './_baseData.js';

const STAFF_TREND = [
  { month: 'Aug', value: 48 }, { month: 'Sep', value: 52 }, { month: 'Oct', value: 54 },
  { month: 'Nov', value: 54 }, { month: 'Dec', value: 53 }, { month: 'Jan', value: 56 },
  { month: 'Feb', value: 57 }, { month: 'Mar', value: 58 },
];
const HIRE_TREND = [
  { month: 'Aug', value: 6 }, { month: 'Sep', value: 2 }, { month: 'Oct', value: 1 },
  { month: 'Nov', value: 0 }, { month: 'Dec', value: 1 }, { month: 'Jan', value: 2 },
  { month: 'Feb', value: 2 }, { month: 'Mar', value: 3 },
];

export default {
  key: 'hr',
  activePath: '/hr-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'HR', name: 'Human Resources', role: 'Operations â€” Staff & Human Resources' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, HR Team!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'HR widgets currently use template snapshots pending live human resources service integration.',
  note: 'Certification remains in review until HR metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/hr/summary/',
  liveDataKey: 'hr',
  metrics: [
    { label: 'Staff Count', value: '58', detail: '42 FT, 16 PT â€” all positions active.', accent: 'blue' },
    { label: 'Open Positions', value: '4', detail: '2 posted, 2 in offer stage â€” targeting May start.', accent: 'gold' },
    { label: 'Onboarding Active', value: '3', detail: '3 new hires â€” first day this week.', accent: 'emerald' },
    { label: 'Compliance Due', value: '6', detail: '6 staff certifications expiring within 60 days.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Complete onboarding for 3 new hires', detail: 'First-day orientation today â€” access, handbook, setup.', state: 'Today', tone: 'warn' },
    { title: 'Renew 6 expiring certifications', detail: 'CPR x4, SafeEnvironments x2 â€” staff notified.', state: 'This week', tone: 'warn' },
    { title: 'Finalize offer for Math Teacher position', detail: 'Candidate accepted verbally â€” contract pending.', state: 'Today', tone: 'nominal' },
  ],
  prioritiesTitle: 'HR priorities',

  alerts: [
    { title: '3 new hires starting this week', detail: 'Orientation scheduled â€” access provisioning in progress.', tone: 'nominal' },
    { title: '6 certifications expiring within 60 days', detail: 'CPR and Safe Environment training renewals needed.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'staffDirectory', icon: 'SD', title: 'Staff Directory', status: 'Current', statusTone: 'good',
      mainKpi: '58 staff â€” 42 FT, 16 PT', summary: 'All positions active â€” 3 new hires onboarding this week.',
      kpis: [{ label: 'Total Staff', value: '58' }, { label: 'Full Time', value: '42' }, { label: 'Part Time', value: '16' }, { label: 'Onboarding', value: '3' }],
      details: ['42 full-time staff across all departments', '16 part-time and contracted staff', '3 new hires in week-1 onboarding', 'Last directory audit: April 15'],
      primaryActionLabel: 'View Directory', backActionLabel: 'Open HR',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:00 AM' },
    { key: 'recruiting', icon: 'RC', title: 'Recruiting', status: 'Active', statusTone: 'warn',
      mainKpi: '4 open positions', summary: '2 in offer stage, 2 still posted â€” targeting May starts.',
      kpis: [{ label: 'Open Positions', value: '4' }, { label: 'In Offer Stage', value: '2' }, { label: 'Interviews Scheduled', value: '3' }, { label: 'Applications', value: '18' }],
      details: ['Math Teacher: offer pending signature', 'PT Librarian: offer extended', 'PE Teacher: 2 interviews scheduled', 'Admissions Coordinator: 16 applicants'],
      primaryActionLabel: 'View Open Positions', backActionLabel: 'Applicant Tracker',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:05 AM' },
    { key: 'onboarding', icon: 'OB', title: 'Onboarding', status: 'Active', statusTone: 'good',
      mainKpi: '3 new hires â€” orientation today', summary: 'All three starting this week â€” access provisioned.',
      kpis: [{ label: 'In Onboarding', value: '3' }, { label: 'Day 1 Today', value: '3' }, { label: 'Checklist Complete', value: '2' }, { label: 'Access Provisioned', value: '3' }],
      details: ['Orientation sessions 8â€“11 AM today', 'Handbook acknowledgment required by EOD', 'System access provisioned for all 3', 'Mentor assigned for each new hire'],
      primaryActionLabel: 'Onboarding Checklist', backActionLabel: 'HR Dashboard',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:10 AM' },
    { key: 'compliance', icon: 'CL', title: 'Compliance', status: 'Watch', statusTone: 'warn',
      mainKpi: '6 certifications expiring', summary: 'CPR x4 + Safe Environment x2 â€” 60-day window.',
      kpis: [{ label: 'Expiring Soon', value: '6' }, { label: 'CPR', value: '4' }, { label: 'Safe Environ.', value: '2' }, { label: 'All Current', value: '52' }],
      details: ['4 CPR certifications expire within 60 days', '2 Safe Environment certs expiring May 15', 'Training scheduled for 4 staff (May 3)', 'Diocese compliance report due June 1'],
      primaryActionLabel: 'View Compliance', backActionLabel: 'Training Records',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:15 AM' },
    { key: 'performance', icon: 'PV', title: 'Performance Reviews', status: 'Upcoming', statusTone: 'good',
      mainKpi: 'Annual reviews start May 15', summary: 'Pre-review packets sent â€” forms due April 30.',
      kpis: [{ label: 'Reviews Due', value: '42' }, { label: 'Self-Evals Due', value: 'Apr 30' }, { label: 'Completed', value: '0' }, { label: 'Cycle', value: 'Annual' }],
      details: ['42 full-time staff annual reviews', 'Self-evaluation forms sent April 10', 'Deadline for forms: April 30', 'Manager review window: May 15â€“30'],
      primaryActionLabel: 'View Reviews', backActionLabel: 'HR Dashboard',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '8:20 AM' },
    { key: 'payroll', icon: 'PY', title: 'Payroll Coordination', status: 'On Track', statusTone: 'good',
      mainKpi: 'Payroll runs April 30', summary: 'Next payroll on schedule â€” 3 new hires added.',
      kpis: [{ label: 'Next Payroll', value: 'Apr 30' }, { label: 'Staff in Payroll', value: '58' }, { label: 'New Hires Added', value: '3' }, { label: 'Adjustments', value: '2' }],
      details: ['58 staff in April 30 payroll run', '3 new hires added to pay cycle', '2 benefit adjustment changes pending', 'Direct deposit verified for all'],
      primaryActionLabel: 'View Payroll', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Staffing levels', title: 'Total Staff Over Time', chip: '58 staff (+21% since Aug)', trend: STAFF_TREND },
    { kicker: 'Hiring velocity', title: 'New Hires Per Month', chip: '3 hires in March', trend: HIRE_TREND },
  ],

  activities: [
    '3 new hire orientations scheduled for today.',
    'Math Teacher offer letter sent â€” verbal acceptance confirmed.',
    '6 certification renewal reminders sent to staff.',
    'Self-evaluation forms distributed for annual review cycle.',
    'April 30 payroll confirmed â€” all 58 staff verified.',
  ],

  quickActions: [
    { label: 'Staff Directory', href: '/hr-dashboard' },
    { label: 'Open Positions', href: '/hr-dashboard' },
    { label: 'Onboarding', href: '/hr-dashboard' },
    { label: 'Compliance Records', href: '/hr-dashboard' },
  ],

  statuses: [
    { label: 'Staff Coverage', state: '58 active' },
    { label: 'Open Positions', state: '4 recruiting' },
    { label: 'Certifications', state: '6 expiring' },
    { label: 'Next Payroll', state: 'April 30' },
  ],
};

