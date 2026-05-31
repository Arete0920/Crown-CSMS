import { BASE_NOTE } from './_baseData.js';

const REQUEST_TREND = [
  { month: 'Sep', value: 6 }, { month: 'Oct', value: 7 }, { month: 'Nov', value: 9 },
  { month: 'Dec', value: 5 }, { month: 'Jan', value: 7 }, { month: 'Feb', value: 8 }, { month: 'Mar', value: 8 },
];
const TRANSCRIPT_TREND = [
  { month: 'Sep', value: 12 }, { month: 'Oct', value: 14 }, { month: 'Nov', value: 16 },
  { month: 'Dec', value: 8 }, { month: 'Jan', value: 18 }, { month: 'Feb', value: 22 }, { month: 'Mar', value: 23 },
];

export default {
  key: 'registrar',
  activePath: '/registrar',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'RG', name: 'Registrar', role: 'Registrar â€” Records & Enrollment' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Registrar!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/registrar/summary/',
  liveDataKey: 'registrar',
  metrics: [
    { label: 'Enrollment Total', value: '412', detail: 'Snapshot Feb 26 â€” verified active enrollment.', accent: 'navy' },
    { label: 'Pending Requests', value: '8', detail: '5 records and 3 enrollment-related items in flight.', accent: 'gold' },
    { label: 'Transcripts Issued (MTD)', value: '23', detail: 'College and transfer requests dominant.', accent: 'blue' },
    { label: 'Active Holds', value: '3', detail: 'Pending financial clearance on three accounts.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Resolve administrative hold on records request', detail: 'Records transfer flagged â€” coordinate with finance.', state: 'Today', tone: 'warn' },
    { title: 'Process 14 college transcripts in queue', detail: 'Average turnaround 2.3 days â€” confirm clearance.', state: 'This week', tone: 'warn' },
    { title: 'Prepare semester-end transcript batch', detail: 'Mar 15 deadline â€” start verification cycle.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Registrar priorities',

  alerts: [
    { title: '1 records request on administrative hold', detail: 'Coordinate clearance with finance to release.', tone: 'warn' },
    { title: '3 enrollment holds pending financial clearance', detail: 'Holds preventing schedule release for impacted students.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'requests', icon: 'RQ', title: 'Pending Requests', status: 'Watch', statusTone: 'warn',
      mainKpi: '8 in queue', summary: 'Mix of enrollment, transcript, transfer, and name change items.',
      kpis: [{ label: 'In progress', value: '1' }, { label: 'Pending', value: '2' }, { label: 'On hold', value: '1' }, { label: 'Complete', value: '1' }],
      details: ['Enrollment Verification â€” submitted Feb 20 (in progress)', 'College Transcript â€” submitted Feb 21 (pending)', 'College Transcript â€” submitted Feb 22 (pending)', 'Records Transfer â€” submitted Feb 18 (hold)'],
      primaryActionLabel: 'Open Request Queue', backActionLabel: 'Hold Review',
      primaryActionHref: '/registrar', backActionHref: '/registrar', lastUpdated: '8:30 AM' },
    { key: 'transcripts', icon: 'TR', title: 'Transcript Queue', status: 'Stable', statusTone: 'good',
      mainKpi: '23 issued MTD / 14 college pending', summary: 'College transcripts dominate the queue; turnaround on plan.',
      kpis: [{ label: 'College/Univ', value: '14' }, { label: 'Transfer Public', value: '4' }, { label: 'Transfer Private', value: '3' }, { label: 'Court / Legal', value: '2' }],
      details: ['College/University â€” 14 in queue / 2.3 d avg', 'Transfer Public â€” 4 in queue / 1.8 d avg', 'Transfer Private â€” 3 in queue / 2.1 d avg', 'Court / Legal â€” 2 in queue / 5.0 d avg'],
      primaryActionLabel: 'Open Transcript Queue', backActionLabel: 'Issued Log',
      primaryActionHref: '/registrar', backActionHref: '/registrar', lastUpdated: '8:15 AM' },
    { key: 'enrollment', icon: 'EN', title: 'Enrollment', status: 'Stable', statusTone: 'good',
      mainKpi: '412 active', summary: 'Verified active enrollment as of Feb 26.',
      kpis: [{ label: 'Total', value: '412' }, { label: 'New this term', value: '18' }, { label: 'Withdrawals', value: '2' }, { label: 'On hold', value: '3' }],
      details: ['New enrollments â€” Grade 7: 6 (100%), Grade 8: 4 (67%)', 'New enrollments â€” Grade 9: 3 (50%), Grade 10: 2 (33%)', 'New enrollments â€” Grade 11: 2 (33%), Grade 12: 1 (17%)', '3 enrollment holds pending financial clearance'],
      primaryActionLabel: 'Open Enrollment', backActionLabel: 'Snapshot Reports',
      primaryActionHref: '/registrar', backActionHref: '/reports', lastUpdated: '8:00 AM' },
    { key: 'records', icon: 'RC', title: 'Records', status: 'Stable', statusTone: 'good',
      mainKpi: 'GPA calculation current', summary: 'Records pipeline current; GPA recalculation done for term.',
      kpis: [{ label: 'GPA status', value: 'Current' }, { label: 'Records issued', value: '23' }, { label: 'Records hold', value: '1' }, { label: 'Pending review', value: '8' }],
      details: ['GPA calculation current for the term', '23 records issued month to date', '1 records request on administrative hold', '8 student records pending review'],
      primaryActionLabel: 'Open Records Console', backActionLabel: 'Audit Log',
      primaryActionHref: '/registrar', backActionHref: '/registrar', lastUpdated: '7:50 AM' },
    { key: 'compliance', icon: 'CM', title: 'Compliance & Verification', status: 'Stable', statusTone: 'good',
      mainKpi: 'All filings current', summary: 'Verifications and state reporting on schedule.',
      kpis: [{ label: 'Filings due wk', value: '0' }, { label: 'Filings done MTD', value: '6' }, { label: 'Verifications', value: '5' }, { label: 'Audit due', value: 'May' }],
      details: ['No filings due this week', '6 filings completed month to date', '5 enrollment verifications issued', 'External records audit scheduled May'],
      primaryActionLabel: 'Compliance Console', backActionLabel: 'Reporting',
      primaryActionHref: '/registrar', backActionHref: '/reports', lastUpdated: '7:35 AM' },
    { key: 'communications', icon: 'CO', title: 'Family Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Status notices current', summary: 'Family notices about records and transcripts on schedule.',
      kpis: [{ label: 'Notices sent wk', value: '6' }, { label: 'Hold letters', value: '3' }, { label: 'Verifications mailed', value: '5' }, { label: 'Pending', value: '2' }],
      details: ['6 family status notices delivered this week', '3 hold letters mailed for clearance', '5 verifications mailed to colleges', '2 family notices pending review'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Notice Library',
      primaryActionHref: '/communications', backActionHref: '/registrar', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Request trend', title: 'Open requests by month', chip: 'Stable', trend: REQUEST_TREND },
    { kicker: 'Transcript trend', title: 'Transcripts issued by month', chip: 'On pace', trend: TRANSCRIPT_TREND },
  ],

  activityKicker: 'Registrar activity',
  activityTitle: 'Recent records events',
  activities: [
    'Enrollment verification submitted Feb 20.',
    'Two college transcript requests received.',
    'Records transfer placed on administrative hold.',
    'Name change request marked complete.',
    'Six family status notices delivered.',
  ],

  quickActions: [
    { title: 'Open Reports', eyebrow: 'Quick action', description: 'Run enrollment, GPA, and transcript reports.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['registrar'] },
    { title: 'Open Gradebook', eyebrow: 'Quick action', description: 'Coordinate GPA recalculations with academics.', actionLabel: 'Open Gradebook', href: '/gradebook', allowedRoles: ['registrar'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Send family status notices and verifications.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['registrar'] },
    { title: 'Open Registrar', eyebrow: 'Quick action', description: 'Return to the Registrar command center.', actionLabel: 'Open Registrar', href: '/registrar', allowedRoles: ['registrar'] },
  ],

  statusTitle: 'Registrar workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Records Pipeline', state: 'Current' },
    { label: 'GPA Calc', state: 'Current' },
    { label: 'Transcript Queue', state: '14 pending' },
    { label: 'Holds', state: '3 active' },
  ],
};

