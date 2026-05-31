import { BASE_NOTE } from './_baseData.js';

const CARE_TREND = [
  { month: 'Aug', value: 8 }, { month: 'Sep', value: 12 }, { month: 'Oct', value: 14 },
  { month: 'Nov', value: 18 }, { month: 'Dec', value: 16 }, { month: 'Jan', value: 22 },
  { month: 'Feb', value: 19 }, { month: 'Mar', value: 24 },
];
const RESOLVE_TREND = [
  { month: 'Aug', value: 88 }, { month: 'Sep', value: 84 }, { month: 'Oct', value: 86 },
  { month: 'Nov', value: 81 }, { month: 'Dec', value: 83 }, { month: 'Jan', value: 87 },
  { month: 'Feb', value: 89 }, { month: 'Mar', value: 91 },
];

export default {
  key: 'studentCare',
  activePath: '/student-care-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'SC', name: 'Student Care Team', role: 'Counseling â€” Student Wellness & Support' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Student Care!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Student care widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until student care metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/studentCare/summary/',
  liveDataKey: 'studentCare',
  metrics: [
    { label: 'At-Risk Students', value: '24', detail: '8 high-priority â€” active care plans in place.', accent: 'gold' },
    { label: 'Interventions Active', value: '17', detail: '12 academic, 5 behavioral â€” all assigned.', accent: 'navy' },
    { label: 'Resolution Rate', value: '91%', detail: 'Best this year â€” 3-year high in positive closures.', accent: 'emerald' },
    { label: 'Family Contacts', value: '38', detail: 'This month â€” 31 documented, 7 pending log.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Review 8 high-priority care plans', detail: 'Weekly team review â€” 3 require updated goals.', state: 'Today', tone: 'warn' },
    { title: 'Log 7 pending family contacts', detail: 'Documentation required within 48 hours of contact.', state: 'Today', tone: 'warn' },
    { title: 'Complete monthly at-risk report', detail: 'Due to principal by April 30.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Care team priorities',

  alerts: [
    { title: 'Student #0831 care plan escalated', detail: 'Behavioral incident â€” parent meeting requested.', tone: 'warn' },
    { title: '3 care plans require goal updates', detail: 'Team review today â€” updates needed before Friday.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'atRisk', icon: 'AR', title: 'At-Risk Roster', status: 'Active', statusTone: 'warn',
      mainKpi: '24 students â€” 8 high-priority', summary: 'All high-priority students have active care plans.',
      kpis: [{ label: 'At-Risk', value: '24' }, { label: 'High Priority', value: '8' }, { label: 'Medium', value: '11' }, { label: 'Monitoring', value: '5' }],
      details: ['8 high-priority students â€” weekly check-ins', '11 medium-risk â€” bi-weekly contact', '5 in monitoring â€” monthly review', 'All have assigned counselors'],
      primaryActionLabel: 'View Roster', backActionLabel: 'Care Plans',
      primaryActionHref: '/student-care-dashboard', backActionHref: '/student-care-dashboard', lastUpdated: '8:00 AM' },
    { key: 'interventions', icon: 'IV', title: 'Interventions', status: 'Active', statusTone: 'good',
      mainKpi: '17 active interventions', summary: '12 academic, 5 behavioral â€” all assigned to staff.',
      kpis: [{ label: 'Active', value: '17' }, { label: 'Academic', value: '12' }, { label: 'Behavioral', value: '5' }, { label: 'Unassigned', value: '0' }],
      details: ['12 academic intervention plans active', '5 behavioral support plans active', 'All interventions assigned to staff', 'Last review: 2 days ago'],
      primaryActionLabel: 'View Interventions', backActionLabel: 'Student List',
      primaryActionHref: '/student-care-dashboard', backActionHref: '/student-care-dashboard', lastUpdated: '8:05 AM' },
    { key: 'carePlans', icon: 'CP', title: 'Care Plans', status: 'Watch', statusTone: 'warn',
      mainKpi: '24 active plans â€” 3 need updates', summary: '3 care plans require updated goals â€” team review today.',
      kpis: [{ label: 'Active Plans', value: '24' }, { label: 'Current', value: '21' }, { label: 'Needs Update', value: '3' }, { label: 'Escalated', value: '1' }],
      details: ['21 care plans current', '3 require updated goals after weekly review', '1 escalated â€” parent meeting requested', 'Next group review: Friday'],
      primaryActionLabel: 'Review Plans', backActionLabel: 'Team Calendar',
      primaryActionHref: '/student-care-dashboard', backActionHref: '/student-care-dashboard', lastUpdated: '8:10 AM' },
    { key: 'familyContact', icon: 'FC', title: 'Family Contacts', status: 'Watch', statusTone: 'warn',
      mainKpi: '38 contacts this month â€” 7 unlogged', summary: '7 contacts need documentation within 48 hrs.',
      kpis: [{ label: 'Contacts', value: '38' }, { label: 'Logged', value: '31' }, { label: 'Pending', value: '7' }, { label: 'Meetings Scheduled', value: '4' }],
      details: ['31 contacts documented in system', '7 contacts pending 48-hr log deadline', '4 parent meetings scheduled this week', 'Average response time: 1.2 days'],
      primaryActionLabel: 'Log Contacts', backActionLabel: 'View Communications',
      primaryActionHref: '/communications-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '7:55 AM' },
    { key: 'counseling', icon: 'CN', title: 'Counseling Sessions', status: 'Stable', statusTone: 'good',
      mainKpi: '64 sessions this month', summary: 'Session volume on track â€” resolution rate 91%.',
      kpis: [{ label: 'Sessions', value: '64' }, { label: 'Individual', value: '48' }, { label: 'Group', value: '16' }, { label: 'Resolution Rate', value: '91%' }],
      details: ['48 individual counseling sessions', '16 group sessions across 4 groups', 'Resolution rate 91% â€” best this year', 'Avg sessions per student: 2.7'],
      primaryActionLabel: 'View Sessions', backActionLabel: 'Counseling Dashboard',
      primaryActionHref: '/counseling-dashboard', backActionHref: '/counseling-dashboard', lastUpdated: '8:15 AM' },
    { key: 'reports', icon: 'RP', title: 'Care Reports', status: 'Due Soon', statusTone: 'warn',
      mainKpi: 'Monthly report due April 30', summary: 'At-risk summary due to principal by end of week.',
      kpis: [{ label: 'Due', value: 'April 30' }, { label: 'At-Risk Count', value: '24' }, { label: 'Interventions', value: '17' }, { label: 'Resolution Rate', value: '91%' }],
      details: ['Monthly at-risk report due April 30', 'Principal review scheduled May 2', 'Board summary included', 'YTD trend data compiled'],
      primaryActionLabel: 'Prepare Report', backActionLabel: 'View History',
      primaryActionHref: '/student-care-dashboard', backActionHref: '/student-care-dashboard', lastUpdated: '8:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Student referrals', title: 'At-Risk Students Over Time', chip: '24 currently tracked', trend: CARE_TREND },
    { kicker: 'Positive closure rate', title: 'Intervention Resolution Rate', chip: '91% this month', trend: RESOLVE_TREND },
  ],

  activities: [
    'Student #0831 care plan escalated â€” parent meeting requested.',
    '3 care plan goal updates flagged for team review.',
    '7 family contacts queued for documentation.',
    'Monthly at-risk report drafted for principal.',
    '64 counseling sessions logged this month.',
  ],

  quickActions: [
    { label: 'View At-Risk Roster', href: '/student-care-dashboard' },
    { label: 'Log Family Contact', href: '/communications-dashboard' },
    { label: 'Counseling', href: '/counseling-dashboard' },
    { label: 'Prepare Report', href: '/student-care-dashboard' },
  ],

  statuses: [
    { label: 'Care Plans', state: '24 active' },
    { label: 'Interventions', state: '17 active' },
    { label: 'Family Contacts', state: '7 pending log' },
    { label: 'Monthly Report', state: 'Due April 30' },
  ],
};

