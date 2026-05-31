import { BASE_NOTE } from './_baseData.js';

const ATTENDANCE_TREND = [
  { month: 'Sep', value: 88 }, { month: 'Oct', value: 87 }, { month: 'Nov', value: 89 },
  { month: 'Dec', value: 86 }, { month: 'Jan', value: 90 }, { month: 'Feb', value: 91 }, { month: 'Mar', value: 90 },
];
const WIN_TREND = [
  { month: 'Sep', value: 50 }, { month: 'Oct', value: 58 }, { month: 'Nov', value: 60 },
  { month: 'Dec', value: 62 }, { month: 'Jan', value: 64 }, { month: 'Feb', value: 65 }, { month: 'Mar', value: 65 },
];

export default {
  key: 'athletics',
  activePath: '/athletics',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'AD', name: 'Athletic Director', role: 'Athletics â€” Teams & Compliance' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Athletic Director!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/athletics/summary/',
  liveDataKey: 'athletics',

  metrics: [
    { label: 'Upcoming Events', value: '6', detail: '2 home / 4 away over next 7 days.', accent: 'navy' },
    { label: 'Eligibility Issues', value: '3', detail: '1 GPA, 1 missing physical, 1 missing consent.', accent: 'gold' },
    { label: 'Active Injuries', value: '2', detail: 'Both have active return-to-play protocols.', accent: 'gold' },
    { label: 'Transportation Needs', value: '4', detail: 'Buses requested across 4 away events.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Resolve eligibility for boys basketball player', detail: 'GPA below 2.0 â€” confirm tutoring plan with academic team.', state: 'Today', tone: 'warn' },
    { title: 'Collect missing physical for football player', detail: 'Cannot participate until form is on file.', state: 'Today', tone: 'warn' },
    { title: 'Confirm transportation for 4 away events', detail: 'Bus requests pending office approval.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Athletics priorities',

  alerts: [
    { title: '3 eligibility issues open', detail: 'Players cannot participate until issues are resolved.', tone: 'warn' },
    { title: '2 active injuries', detail: 'Return-to-play protocols in flight â€” coordinate with nurse.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'schedule', icon: 'SC', title: 'Upcoming Schedule', status: 'Stable', statusTone: 'good',
      mainKpi: '6 events in next 7 days', summary: 'Schedule confirmed; transportation pending for 4 away events.',
      kpis: [{ label: 'Events', value: '6' }, { label: 'Home', value: '2' }, { label: 'Away', value: '4' }, { label: 'Transport', value: '4 needed' }],
      details: ['Feb 22 â€” Boys Basketball â€” Home', 'Feb 23 â€” Girls Soccer â€” Away', 'Feb 24 â€” Track Meet â€” Away', 'Feb 25 â€” Boys Basketball â€” Away'],
      primaryActionLabel: 'Open Schedule', backActionLabel: 'Transportation',
      primaryActionHref: '/athletics', backActionHref: '/office', lastUpdated: '8:30 AM' },
    { key: 'eligibility', icon: 'EL', title: 'Eligibility', status: 'Watch', statusTone: 'warn',
      mainKpi: '3 issues open', summary: 'GPA and paperwork issues are blocking three players from participation.',
      kpis: [{ label: 'Open issues', value: '3' }, { label: 'GPA holds', value: '1' }, { label: 'Missing physical', value: '1' }, { label: 'Missing consent', value: '1' }],
      details: ['Boys Basketball â€” GPA below 2.0', 'Football â€” missing physical form', 'Track â€” missing parent consent', '90% of athletes currently eligible'],
      primaryActionLabel: 'Open Eligibility Console', backActionLabel: 'Academic Coord.',
      primaryActionHref: '/athletics', backActionHref: '/gradebook', lastUpdated: '8:15 AM' },
    { key: 'rosters', icon: 'RO', title: 'Roster Compliance', status: 'Stable', statusTone: 'good',
      mainKpi: 'All sports rostered', summary: 'Forms and physicals tracked across all teams.',
      kpis: [{ label: 'Boys BB', value: '12' }, { label: 'Girls Soccer', value: '16' }, { label: 'Track', value: '22' }, { label: 'Swimming', value: '14' }],
      details: ['Boys Basketball â€” 12 athletes / forms current', 'Girls Soccer â€” 16 athletes / forms current', 'Track â€” 22 athletes / 1 missing form', 'Swimming â€” 14 athletes / forms current'],
      primaryActionLabel: 'Open Rosters', backActionLabel: 'Form Library',
      primaryActionHref: '/athletics', backActionHref: '/athletics', lastUpdated: '8:00 AM' },
    { key: 'injuries', icon: 'IJ', title: 'Injuries & Health', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 active injury cases', summary: 'Both injuries on return-to-play protocol with the nurse.',
      kpis: [{ label: 'Active', value: '2' }, { label: 'Cleared MTD', value: '3' }, { label: 'On RTP plan', value: '2' }, { label: 'Athletic trainer', value: 'On site' }],
      details: ['2 athletes on active injury protocol', '3 athletes cleared this month', 'Return-to-play coordination with nurse', 'Athletic trainer on site Tue/Thu'],
      primaryActionLabel: 'Open Injury Log', backActionLabel: 'Nurse Coord.',
      primaryActionHref: '/athletics', backActionHref: '/health', lastUpdated: '7:50 AM' },
    { key: 'performance', icon: 'PF', title: 'Team Performance', status: 'Stable', statusTone: 'good',
      mainKpi: '65% win rate', summary: 'Programs performing within plan across boys and girls teams.',
      kpis: [{ label: 'Teams', value: '6' }, { label: 'Win rate', value: '65%' }, { label: 'Games week', value: '2' }, { label: 'Athletes eligible', value: '90%' }],
      details: ['6 active teams in season', '65% combined win rate season to date', '2 games scheduled this week', '90% of athletes currently eligible'],
      primaryActionLabel: 'Performance Reports', backActionLabel: 'Open Athletics',
      primaryActionHref: '/reports', backActionHref: '/athletics', lastUpdated: '7:35 AM' },
    { key: 'communications', icon: 'CO', title: 'Athletics Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Weekly recap sent', summary: 'Game recaps and family notices delivered on schedule.',
      kpis: [{ label: 'Recaps sent', value: '1' }, { label: 'Family notices', value: '3' }, { label: 'Press updates', value: '1' }, { label: 'Pending', value: '1' }],
      details: ['Weekly recap sent to athletics families', '3 game-day notices going out this week', '1 press update on basketball recap', '1 transportation reminder pending'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Newsletter',
      primaryActionHref: '/communications', backActionHref: '/athletics', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Eligibility trend', title: 'Athletes eligible % by month', chip: 'On target', trend: ATTENDANCE_TREND },
    { kicker: 'Win-rate trend', title: 'Combined win rate % by month', chip: 'Climbing', trend: WIN_TREND },
  ],

  activityKicker: 'Athletics activity',
  activityTitle: 'Recent athletics events',
  activities: [
    'Boys Basketball home game scheduled for Feb 22.',
    'Bus request submitted for Track meet Feb 24.',
    'Athlete cleared from injury protocol â€” soccer.',
    'Eligibility flag opened for football player.',
    'Weekly athletics recap sent to families.',
  ],

  quickActions: [
    { title: 'Open Gradebook', eyebrow: 'Quick action', description: 'Coordinate eligibility GPA reviews with academics.', actionLabel: 'Open Gradebook', href: '/gradebook', allowedRoles: ['athletics'] },
    { title: 'Open Health', eyebrow: 'Quick action', description: 'Coordinate injury return-to-play protocols.', actionLabel: 'Open Health', href: '/health', allowedRoles: ['athletics'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Send game-day notices and recap newsletters.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['athletics'] },
    { title: 'Open Athletics', eyebrow: 'Quick action', description: 'Return to the Athletics command center.', actionLabel: 'Open Athletics', href: '/athletics', allowedRoles: ['athletics'] },
  ],

  statusTitle: 'Athletics workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Eligibility', state: 'Watch' },
    { label: 'Roster Forms', state: '99%' },
    { label: 'Transportation', state: '4 pending' },
    { label: 'Injury Protocol', state: 'Active' },
  ],
};
