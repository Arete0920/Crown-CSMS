import { BASE_NOTE } from './_baseData.js';

const MILESTONE_TREND = [
  { month: 'Aug', value: 2 }, { month: 'Sep', value: 8 }, { month: 'Oct', value: 14 },
  { month: 'Nov', value: 18 }, { month: 'Dec', value: 20 }, { month: 'Jan', value: 24 },
  { month: 'Feb', value: 28 }, { month: 'Mar', value: 34 },
];
const SCHOOL_TREND = [
  { month: 'Aug', value: 2 }, { month: 'Sep', value: 4 }, { month: 'Oct', value: 6 },
  { month: 'Nov', value: 7 }, { month: 'Dec', value: 8 }, { month: 'Jan', value: 9 },
  { month: 'Feb', value: 11 }, { month: 'Mar', value: 12 },
];

export default {
  key: 'implementationSuccess',
  activePath: '/implementation-success-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'IS', name: 'Implementation Success', role: 'Platform â€” School Onboarding & Launch Management' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Implementation Team!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/implementationSuccess/summary/',
  liveDataKey: 'implementationSuccess',

  metrics: [
    { label: 'Schools Onboarding', value: '12', detail: '12 schools in active implementation phases.', accent: 'blue' },
    { label: 'Milestones Completed', value: '34', detail: 'Of 48 planned this semester â€” on pace.', accent: 'emerald' },
    { label: 'Active Blockers', value: '3', detail: '3 blockers requiring escalation this week.', accent: 'gold' },
    { label: 'Go-Lives YTD', value: '9', detail: '9 schools fully live â€” 3 more targeted this quarter.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Resolve 3 active implementation blockers', detail: 'Data migration, SSO config, and roster import â€” all blocking go-live.', state: 'Today', tone: 'warn' },
    { title: 'Confirm Q2 go-live dates for 3 schools', detail: 'Jefferson, Covenant, Grace â€” targeting May 1 go-live.', state: 'This week', tone: 'nominal' },
    { title: 'Deliver onboarding kickoff for Westside Prep', detail: 'New school kickoff call scheduled April 12.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Implementation priorities',

  alerts: [
    { title: '3 blockers risking May 1 go-live dates', detail: 'Escalate data migration, SSO, and roster issues today.', tone: 'warn' },
    { title: 'Westside Prep kickoff April 12', detail: 'Prep kickoff materials and agenda â€” first school of Q2 cohort.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'pipeline', icon: 'PL', title: 'School Pipeline', status: 'Active', statusTone: 'good',
      mainKpi: '12 schools â€” 9 live, 3 in final phase', summary: 'Healthy pipeline â€” Q2 cohort adds Westside Prep.',
      kpis: [{ label: 'In Progress', value: '12' }, { label: 'Live YTD', value: '9' }, { label: 'Final Phase', value: '3' }, { label: 'Q2 Cohort', value: '4' }],
      details: ['12 schools in active onboarding', '9 schools fully live YTD', '3 schools in final go-live phase', '4 schools in Q2 onboarding cohort'],
      primaryActionLabel: 'View Pipeline', backActionLabel: 'School Status',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:00 AM' },
    { key: 'milestones', icon: 'MS', title: 'Milestones', status: 'On Pace', statusTone: 'good',
      mainKpi: '34/48 milestones complete', summary: 'On pace â€” 14 remaining in current semester.',
      kpis: [{ label: 'Complete', value: '34' }, { label: 'Total', value: '48' }, { label: 'On Track', value: '11' }, { label: 'At Risk', value: '3' }],
      details: ['34 of 48 semester milestones complete', '11 schools on pace for milestone delivery', '3 schools have at-risk milestones', 'Next major milestone batch due May 1'],
      primaryActionLabel: 'Milestone Tracker', backActionLabel: 'School Detail',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:05 AM' },
    { key: 'blockers', icon: 'BK', title: 'Blockers', status: 'Action Required', statusTone: 'warn',
      mainKpi: '3 active blockers', summary: 'All 3 blocking May 1 go-lives â€” escalate today.',
      kpis: [{ label: 'Active', value: '3' }, { label: 'Critical', value: '3' }, { label: 'Days Open', value: '4' }, { label: 'Owner', value: 'Tech+Data' }],
      details: ['Blocker 1: Jefferson data migration â€” batch import failing', 'Blocker 2: Covenant SSO config â€” district IT unresponsive', 'Blocker 3: Grace roster import â€” file format mismatch', 'All three block May 1 go-live'],
      primaryActionLabel: 'Resolve Blockers', backActionLabel: 'Escalate',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:10 AM' },
    { key: 'golive', icon: 'GL', title: 'Go-Lives', status: 'On Track', statusTone: 'good',
      mainKpi: '3 go-lives targeted May 1', summary: 'Jefferson, Covenant, Grace â€” contingent on blocker resolution.',
      kpis: [{ label: 'Target Date', value: 'May 1' }, { label: 'Schools', value: '3' }, { label: 'Blockers', value: '3' }, { label: 'YTD Go-Lives', value: '9' }],
      details: ['Jefferson, Covenant, Grace targeting May 1', '9 schools went live YTD', 'Blockers must be resolved by April 22', 'Launch day runbook prepared'],
      primaryActionLabel: 'Go-Live Plan', backActionLabel: 'Checklist',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:15 AM' },
    { key: 'training', icon: 'TR', title: 'Training', status: 'Active', statusTone: 'good',
      mainKpi: '24 training sessions delivered this month', summary: 'All admin and faculty training on schedule.',
      kpis: [{ label: 'Sessions', value: '24' }, { label: 'Users Trained', value: '186' }, { label: 'Satisfaction', value: '4.6/5' }, { label: 'Pending', value: '8' }],
      details: ['24 training sessions delivered in March', '186 users trained this month', '4.6/5 average satisfaction score', '8 sessions pending for Q2 cohort'],
      primaryActionLabel: 'Training Schedule', backActionLabel: 'User Completion',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:20 AM' },
    { key: 'health', icon: 'HE', title: 'Account Health', status: 'Good', statusTone: 'good',
      mainKpi: '9 live accounts â€” all healthy', summary: 'All live schools in healthy operational state.',
      kpis: [{ label: 'Live Schools', value: '9' }, { label: 'Healthy', value: '9' }, { label: 'At Risk', value: '0' }, { label: 'Escalations', value: '0' }],
      details: ['All 9 live schools at healthy account status', 'Zero critical support escalations this month', 'Average daily active users: 248 per school', 'Monthly check-in calls completed for all 9'],
      primaryActionLabel: 'Account Health', backActionLabel: 'Support',
      primaryActionHref: '/implementation-success-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Implementation progress', title: 'Milestones Completed (Cumulative)', chip: '34 this semester', trend: MILESTONE_TREND },
    { kicker: 'Schools in active implementation', title: 'Schools in Onboarding Pipeline', chip: '12 active', trend: SCHOOL_TREND },
  ],

  activities: [
    '3 active blockers flagged for escalation â€” risk to May 1 go-live.',
    'Westside Prep kickoff call confirmed April 12.',
    '34 of 48 semester milestones complete â€” on pace.',
    '24 training sessions delivered in March â€” 186 users trained.',
    'All 9 live school accounts confirmed healthy.',
  ],

  quickActions: [
    { label: 'Blocker Log', href: '/implementation-success-dashboard' },
    { label: 'School Pipeline', href: '/implementation-success-dashboard' },
    { label: 'Go-Live Plan', href: '/implementation-success-dashboard' },
    { label: 'Training Schedule', href: '/implementation-success-dashboard' },
  ],

  statuses: [
    { label: 'Schools Active', state: '12 in progress' },
    { label: 'Blockers', state: '3 active (critical)' },
    { label: 'May 1 Go-Lives', state: '3 targeted' },
    { label: 'Live Schools', state: '9 (all healthy)' },
  ],
};
