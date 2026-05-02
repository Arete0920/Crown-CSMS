import { BASE_NOTE } from './_baseData.js';

const ABSENCE_TREND = [
  { month: 'Sep', value: 4 }, { month: 'Oct', value: 3 }, { month: 'Nov', value: 5 },
  { month: 'Dec', value: 4 }, { month: 'Jan', value: 3 }, { month: 'Feb', value: 3 }, { month: 'Mar', value: 3 },
];
const REQUEST_TREND = [
  { month: 'Sep', value: 9 }, { month: 'Oct', value: 8 }, { month: 'Nov', value: 11 },
  { month: 'Dec', value: 6 }, { month: 'Jan', value: 7 }, { month: 'Feb', value: 7 }, { month: 'Mar', value: 7 },
];

export default {
  key: 'office',
  activePath: '/office',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'OF', name: 'Office Manager', role: 'Office & HR — Operations & Compliance' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Office!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Staff Absent Today', value: '3', detail: 'Substitutes placed for 2 of 3 absences.', accent: 'gold' },
    { label: 'Coverage Gaps', value: '1', detail: 'Period 3 sub still needed.', accent: 'gold' },
    { label: 'Open Requests', value: '7', detail: '3 high priority across facilities and HR.', accent: 'navy' },
    { label: 'HR Tasks Due', value: '4', detail: 'Compliance and onboarding items pending.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Place Period 3 substitute', detail: 'Coverage gap unresolved — assign before second period.', state: 'Today', tone: 'warn' },
    { title: 'Approve background check for new hire', detail: 'In review — finalize before onboarding paperwork.', state: 'Today', tone: 'warn' },
    { title: 'Complete 4 HR compliance tasks', detail: 'TB tests, I-9 reverification, handbook acknowledgments due.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Office priorities',

  alerts: [
    { title: '1 coverage gap — Period 3 sub needed', detail: 'Substitute pool exhausted for that slot — escalate to admin.', tone: 'warn' },
    { title: '2 compliance items due this week', detail: 'TB tests and I-9 reverification on the calendar.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'staff', icon: 'ST', title: 'Staff & Attendance', status: 'Watch', statusTone: 'warn',
      mainKpi: '3 absent / 1 gap', summary: '3 staff absent today, 2 covered by subs. 1 coverage gap remains.',
      kpis: [{ label: 'Absent today', value: '3' }, { label: 'Subs placed', value: '2' }, { label: 'Coverage gaps', value: '1' }, { label: 'On leave', value: '1' }],
      details: ['3 staff absent today across the building', '2 substitutes placed and confirmed', 'Period 3 coverage still needed', 'T. Williams approved leave starts Monday'],
      primaryActionLabel: 'Open Staff Console', backActionLabel: 'Sub Pool',
      primaryActionHref: '/office', backActionHref: '/office', lastUpdated: '8:30 AM' },
    { key: 'requests', icon: 'RQ', title: 'Operational Requests', status: 'Stable', statusTone: 'good',
      mainKpi: '7 open / 3 high', summary: 'Facilities, supplies, and vendor requests under review.',
      kpis: [{ label: 'Open', value: '7' }, { label: 'High priority', value: '3' }, { label: 'Approved this week', value: '4' }, { label: 'Pending vendor', value: '2' }],
      details: ['Facility repair: gym HVAC (high)', 'Supply order: classroom consumables (pending)', 'Background check: new hire (in review, high)', 'Leave request: T. Williams (approved)'],
      primaryActionLabel: 'Open Requests', backActionLabel: 'Vendor Queue',
      primaryActionHref: '/office', backActionHref: '/finance', lastUpdated: '8:15 AM' },
    { key: 'hr', icon: 'HR', title: 'HR Tasks', status: 'Watch', statusTone: 'warn',
      mainKpi: '4 tasks due', summary: 'Compliance and onboarding items pending across staff.',
      kpis: [{ label: 'Tasks due', value: '4' }, { label: 'Onboarding open', value: '1' }, { label: 'Acknowledgments', value: '4 pending' }, { label: 'Reviews due', value: '2' }],
      details: ['Annual TB test due — 2 staff (Feb 28)', 'I-9 reverification — 1 staff (Mar 5)', 'Handbook acknowledgment — 4 staff (Mar 10)', 'Emergency contact update (Mar 15)'],
      primaryActionLabel: 'Open HR Console', backActionLabel: 'Compliance Log',
      primaryActionHref: '/office', backActionHref: '/office', lastUpdated: '8:00 AM' },
    { key: 'compliance', icon: 'CM', title: 'Compliance', status: 'Watch', statusTone: 'warn',
      mainKpi: '2 items due this week', summary: 'Compliance items on track — items closing this week.',
      kpis: [{ label: 'Items due week', value: '2' }, { label: 'Items overdue', value: '0' }, { label: 'Audits scheduled', value: '1' }, { label: 'Closed MTD', value: '6' }],
      details: ['No overdue compliance items', '2 items closing this week', 'Annual audit scheduled May 12', '6 compliance items closed this month'],
      primaryActionLabel: 'Open Compliance', backActionLabel: 'Audit Log',
      primaryActionHref: '/office', backActionHref: '/office', lastUpdated: '7:50 AM' },
    { key: 'facilities', icon: 'FC', title: 'Facilities', status: 'Watch', statusTone: 'warn',
      mainKpi: 'Gym HVAC repair open', summary: 'High-priority facility request in vendor queue.',
      kpis: [{ label: 'Open work orders', value: '4' }, { label: 'High priority', value: '1' }, { label: 'Vendor visits', value: '2 wk' }, { label: 'Closed this week', value: '5' }],
      details: ['Gym HVAC repair scheduled this week', '4 open work orders in facilities queue', '2 vendor visits scheduled', '5 work orders closed this week'],
      primaryActionLabel: 'Facilities Console', backActionLabel: 'Vendor Schedule',
      primaryActionHref: '/office', backActionHref: '/finance', lastUpdated: '7:35 AM' },
    { key: 'communications', icon: 'CO', title: 'Office Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Memos current', summary: 'Internal memos and staff notices on schedule.',
      kpis: [{ label: 'Memos sent week', value: '3' }, { label: 'Staff notices', value: '2' }, { label: 'Pending notices', value: '1' }, { label: 'Family updates', value: '1' }],
      details: ['3 internal memos delivered this week', '2 staff notices posted', '1 family update pending review', 'Bell schedule reminder going out Friday'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Memo Archive',
      primaryActionHref: '/communications', backActionHref: '/office', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Absence trend', title: 'Daily staff absences (avg by month)', chip: 'Steady', trend: ABSENCE_TREND },
    { kicker: 'Open request trend', title: 'Open operational requests by month', chip: 'Stable', trend: REQUEST_TREND },
  ],

  activityKicker: 'Office activity',
  activityTitle: 'Recent operations events',
  activities: [
    'Substitute placed for two morning absences.',
    'Background check submitted for new hire.',
    'Leave request approved for T. Williams.',
    'Vendor invoice received from janitorial service.',
    '5 facility work orders closed this week.',
  ],

  quickActions: [
    { title: 'Open Communications', eyebrow: 'Quick action', description: 'Send memos and staff notices.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['office'] },
    { title: 'Open Finance', eyebrow: 'Quick action', description: 'Review vendor invoices and operational spend.', actionLabel: 'Open Finance', href: '/finance', allowedRoles: ['office'] },
    { title: 'Reports', eyebrow: 'Quick action', description: 'Run absence and operations reports.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['office'] },
    { title: 'Open Office', eyebrow: 'Quick action', description: 'Return to the Office & HR command center.', actionLabel: 'Open Office', href: '/office', allowedRoles: ['office'] },
  ],

  statusTitle: 'Office workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Sub Pool', state: 'Active' },
    { label: 'Vendor Schedule', state: 'On track' },
    { label: 'Compliance Log', state: 'Current' },
    { label: 'HR System', state: 'Synced' },
  ],
};
