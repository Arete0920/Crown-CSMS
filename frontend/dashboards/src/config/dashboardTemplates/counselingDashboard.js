import { BASE_NOTE } from './_baseData.js';

const REFERRAL_TREND = [
  { month: 'Sep', value: 7 }, { month: 'Oct', value: 9 }, { month: 'Nov', value: 8 },
  { month: 'Dec', value: 10 }, { month: 'Jan', value: 11 }, { month: 'Feb', value: 12 }, { month: 'Mar', value: 11 },
];
const RESOLVED_TREND = [
  { month: 'Sep', value: 6 }, { month: 'Oct', value: 8 }, { month: 'Nov', value: 9 },
  { month: 'Dec', value: 10 }, { month: 'Jan', value: 11 }, { month: 'Feb', value: 12 }, { month: 'Mar', value: 12 },
];

export default {
  key: 'counseling',
  activePath: '/counseling',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'CN', name: 'Counseling Team', role: 'Counseling â€” Behavior & Wellness' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Counselors!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/counseling/summary/',
  liveDataKey: 'counseling',

  metrics: [
    { label: 'Referrals This Week', value: '11', detail: '+1 vs last week â€” discipline trend stable.', accent: 'gold' },
    { label: 'Active Plans', value: '8', detail: 'Behavior and academic plans currently in flight.', accent: 'navy' },
    { label: 'Detentions This Week', value: '5', detail: 'Within normal range for term.', accent: 'blue' },
    { label: 'Suspensions This Week', value: '1', detail: 'Pending VP review.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Close 2 overdue follow-up meetings', detail: 'Both scheduled this week â€” confirm parent availability.', state: 'This week', tone: 'warn' },
    { title: 'Convene parent meeting for Tyler Green', detail: '3rd truancy this semester â€” schedule with attendance.', state: 'Today', tone: 'warn' },
    { title: 'Review repeat referral â€” Marcus Brown', detail: '2nd referral in 5 days â€” escalate to behavior plan.', state: 'Today', tone: 'warn' },
  ],
  prioritiesTitle: 'Counseling priorities',

  alerts: [
    { title: '2 follow-up meetings overdue', detail: 'Both meetings need scheduling and parent confirmation.', tone: 'warn' },
    { title: '1 suspension pending VP review', detail: 'Review queued for end-of-day administrator approval.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'referrals', icon: 'RF', title: 'Recent Referrals', status: 'Watch', statusTone: 'warn',
      mainKpi: '11 this week', summary: 'Recent referral mix balanced across behavior and wellness categories.',
      kpis: [{ label: 'This week', value: '11' }, { label: 'Open', value: '5' }, { label: 'Plan active', value: '4' }, { label: 'Resolved', value: '2' }],
      details: ['Marcus Brown (G8) â€” disruptive behavior â€” open', 'Tyler Green (G10) â€” truancy â€” open', 'Aisha Patel (G9) â€” academic concern â€” plan active', 'Chloe Rivera (G11) â€” anxiety â€” plan active'],
      primaryActionLabel: 'Open Referral Queue', backActionLabel: 'Resolved Cases',
      primaryActionHref: '/counseling', backActionHref: '/counseling', lastUpdated: '8:30 AM' },
    { key: 'caseload', icon: 'CL', title: 'Case Load', status: 'Stable', statusTone: 'good',
      mainKpi: '7 open across 2 counselors', summary: 'Caseload balanced â€” Okafor 4 open, Cruz 3 open.',
      kpis: [{ label: 'J. Okafor open', value: '4' }, { label: 'M. Cruz open', value: '3' }, { label: 'Plans active', value: '5' }, { label: 'Resolved MTD', value: '12' }],
      details: ['J. Okafor â€” 4 open / 3 plans / 7 resolved', 'M. Cruz â€” 3 open / 2 plans / 5 resolved', 'New caseload assignments balanced this week', 'Monthly caseload review scheduled Friday'],
      primaryActionLabel: 'Open Case Load', backActionLabel: 'Counselor Schedule',
      primaryActionHref: '/counseling', backActionHref: '/counseling', lastUpdated: '8:15 AM' },
    { key: 'behavior', icon: 'BH', title: 'Behavior Categories', status: 'Stable', statusTone: 'good',
      mainKpi: 'Disruptive behavior leads at 4', summary: 'Category mix typical â€” disruptive and truancy lead.',
      kpis: [{ label: 'Disruptive', value: '4' }, { label: 'Truancy / late', value: '3' }, { label: 'Academic', value: '2' }, { label: 'Wellness', value: '1' }],
      details: ['Disruptive behavior â€” 4 referrals', 'Truancy / late â€” 3 referrals', 'Academic concern â€” 2 referrals', 'Bullying â€” 1 / wellness â€” 1'],
      primaryActionLabel: 'Open Behavior Report', backActionLabel: 'Trends',
      primaryActionHref: '/reports', backActionHref: '/counseling', lastUpdated: '8:00 AM' },
    { key: 'discipline', icon: 'DC', title: 'Discipline Actions', status: 'Watch', statusTone: 'warn',
      mainKpi: '5 detentions / 1 suspension', summary: 'Detention pace within range; suspension under VP review.',
      kpis: [{ label: 'Detentions wk', value: '5' }, { label: 'Suspensions wk', value: '1' }, { label: 'In-school', value: '2' }, { label: 'Pending review', value: '1' }],
      details: ['5 detentions assigned this week', '1 suspension pending VP review', '2 in-school dispositions logged', 'No expulsions in current term'],
      primaryActionLabel: 'Discipline Console', backActionLabel: 'VP Review Queue',
      primaryActionHref: '/counseling', backActionHref: '/counseling', lastUpdated: '7:50 AM' },
    { key: 'wellness', icon: 'WL', title: 'Wellness & Pastoral Care', status: 'Stable', statusTone: 'good',
      mainKpi: '4 active wellness plans', summary: 'Wellness plans coordinated with chaplaincy and families.',
      kpis: [{ label: 'Wellness plans', value: '4' }, { label: 'Pastoral handoffs', value: '2' }, { label: 'Family contacts', value: '8' }, { label: 'Group support', value: '2' }],
      details: ['4 active wellness / anxiety plans', '2 pastoral care handoffs to chaplain', '8 family contacts logged this week', '2 group support sessions running'],
      primaryActionLabel: 'Wellness Console', backActionLabel: 'Pastoral Coord.',
      primaryActionHref: '/counseling', backActionHref: '/spiritual-life', lastUpdated: '7:35 AM' },
    { key: 'communications', icon: 'CO', title: 'Counseling Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Family contacts current', summary: '8 family contacts this week. Documentation up to date.',
      kpis: [{ label: 'Family contacts', value: '8' }, { label: 'Letters sent', value: '3' }, { label: 'Notes filed', value: '14' }, { label: 'Pending', value: '1' }],
      details: ['8 family contacts logged this week', '3 letters mailed to families', '14 case notes filed', '1 pending family contact this afternoon'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Case Note Library',
      primaryActionHref: '/communications', backActionHref: '/counseling', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Referral trend', title: 'Weekly referrals by month', chip: 'Stable', trend: REFERRAL_TREND },
    { kicker: 'Resolved trend', title: 'Cases resolved by month', chip: 'On pace', trend: RESOLVED_TREND },
  ],

  activityKicker: 'Counseling activity',
  activityTitle: 'Recent counseling events',
  activities: [
    'Marcus Brown referral filed for disruptive behavior.',
    'Aisha Patel academic plan moved to active status.',
    'Noah Williams bullying case resolved with restorative meeting.',
    'Chloe Rivera anxiety wellness plan reviewed.',
    '8 family contacts logged across the team.',
  ],

  quickActions: [
    { title: 'Open Spiritual Life', eyebrow: 'Quick action', description: 'Coordinate pastoral handoffs and care plans.', actionLabel: 'Open Spiritual Life', href: '/spiritual-life', allowedRoles: ['counseling'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Send family letters and follow-ups.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['counseling'] },
    { title: 'Reports', eyebrow: 'Quick action', description: 'Review behavior and discipline trend reports.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['counseling'] },
    { title: 'Open Counseling', eyebrow: 'Quick action', description: 'Return to the Counseling command center.', actionLabel: 'Open Counseling', href: '/counseling', allowedRoles: ['counseling'] },
  ],

  statusTitle: 'Counseling workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Case Notes', state: 'Synced' },
    { label: 'Referral Queue', state: 'Current' },
    { label: 'VP Review Queue', state: 'Watch' },
    { label: 'Family Contact Log', state: 'Up to date' },
  ],
};
